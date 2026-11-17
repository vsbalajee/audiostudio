/** Audio Studio's stateless, read-only MCP entry point on Cloudflare Workers.
 * No media uploads, third-party AI calls or server-side audio rendering.
 * Open the designed browser interface via the returned URL (user click required).
 * All tools currently accept only public/non-sensitive project metadata.
 */
import { McpServer, createMcpHandler } from "@modelcontextprotocol/server";
import { z } from "zod";

type WorkerEnv = { ASSETS: { fetch: (request: Request) => Promise<Response> } };
const defaults = {
  project_name: "My Audio Project",
  gap_seconds: 3,
  music_level: "quiet",
  gentle_cleanup: true,
  normalize_voice: true,
  mute_music_during_final_voice: true
} as const;


/** Stateless chat project: no recordings, secrets or account data are stored. */
const projectSchema = z.object({
  project_name: z.string().trim().min(1).max(120).default("My Audio Project"),
  voice_files: z.array(z.string().trim().min(1).max(240)).max(30).default([]),
  music_file: z.string().trim().max(240).default(""),
  music_level: z.enum(["very quiet", "quiet", "balanced", "prominent"]).default("quiet"),
  after_intro_seconds: z.number().finite().min(0).max(120).default(3),
  between_seconds: z.number().finite().min(0).max(120).default(3),
  outro_seconds: z.number().finite().min(0).max(120).default(5),
  music_under_intro: z.boolean().default(false),
  mute_music_during_final_voice: z.boolean().default(true),
  gentle_cleanup: z.boolean().default(true),
  normalize_voice: z.boolean().default(true),
  denoise_voice: z.boolean().default(false),
  export_stems: z.boolean().default(false),
  additional_instructions: z.string().max(2000).default("")
});
type Project = z.infer<typeof projectSchema>;
function resultForProject(origin: string, project: Project) {
  const link = new URL("/", origin);
  link.searchParams.set("config", JSON.stringify(project));
  return {
    project,
    app_url: link.toString(),
    instructions: "Open the browser link and select your local audio files. Chat changes filenames and configuration only; this tool cannot read, delete or modify local audio bytes. For subsequent chat edits pass the complete current project JSON.",
    audio_engine: "Browser MP3 export after selecting local files and previewing the timeline."
  };
}
function projectAnswer(value: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(value) }] };
}
function projectError(message: string) {
  return { isError: true, content: [{ type: "text" as const, text: message }] };
}

function createServer(origin: string) {
  const server = new McpServer({ name: "audio-studio", version: "2.1.0-preview" });

  server.registerTool("start_audio_studio", {
    description: "Start Audio Studio and return the URL of the real, branded browser form. The assistant should present a clickable Open Audio Studio link; it cannot automatically open a new browser tab. No audio files are sent through this MCP tool.",
    inputSchema: z.object({
      project_name: z.string().trim().min(1).max(120).optional()
    })
  }, async ({ project_name }) => {
    const name = project_name || defaults.project_name;
    const url = new URL("/", origin);
    url.searchParams.set("project", name);
    return { content: [{ type: "text", text: JSON.stringify({
      app_url: url.toString(),
      action: "Offer the user an Open Audio Studio link. Ask them to open it to upload audio.",
      project_name: name,
      defaults,
      status: "browser_form_ready",
      processing_note: "Browser MP3 rendering available on supported local files after timeline preview. Audio bytes never reach MCP."
    }) }] };
  });

  server.registerTool("get_audio_studio_defaults", {
    description: "Return supported default settings and audio-rendering limitations for Audio Studio. This tool does not access private files."
  }, async () => ({ content: [{ type: "text", text: JSON.stringify({
    defaults,
    accepted_audio_extensions: [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".mp4"],
    browser_form_url: origin + "/",
    mcp_version: "2.1.0-preview",
    server_side_audio_rendering: false,
    file_uploads_to_cloudflare: false
  }) }] }));

  server.registerTool("preview_audio_timeline", {
    description: "Calculate a reliable clip timeline from caller-supplied real measured durations. Does not inspect recordings, infer missing durations or render MP3.",
    inputSchema: z.object({
      clips: z.array(z.object({
        name: z.string().trim().min(1).max(240),
        duration_seconds: z.number().finite().positive().max(43200)
      })).min(1).max(100),
      gap_seconds: z.number().finite().min(0).max(120).default(3),
      outro_seconds: z.number().finite().min(0).max(120).default(0)
    })
  }, async ({ clips, gap_seconds, outro_seconds }) => {
    let cursor = 0;
    const timeline = clips.map((clip, index) => {
      if (index) cursor += gap_seconds;
      const item = { clip: clip.name, start_seconds: Number(cursor.toFixed(3)), duration_seconds: clip.duration_seconds };
      cursor += clip.duration_seconds;
      return item;
    });
    return { content: [{ type: "text", text: JSON.stringify({
      timeline,
      gap_seconds,
      outro_seconds,
      total_seconds: Number((cursor + outro_seconds).toFixed(3)),
      note: "Durations came from the caller; MCP did not inspect or process audio."
    }) }] };
  });


  server.registerTool("create_audio_project", {
    description: "Create an Audio Studio project plan in chat: ordered recording filenames, background music filename and mixing preferences. Returns the complete project JSON and a prefilled browser link. Does not read or upload local files.",
    inputSchema: z.object({ project: projectSchema })
  }, async ({ project }) => projectAnswer(resultForProject(origin, project)));

  server.registerTool("edit_audio_project", {
    description: "Edit a previously returned project in chat: add/remove/move a voice filename, change background music filename, or update a mixing setting. Stateless: pass the full current project JSON each time. Returns revised JSON and a prefilled browser link. File selection still happens locally in the browser.",
    inputSchema: z.object({
      project: projectSchema,
      action: z.enum(["add_voice", "remove_voice", "move_voice", "set_music", "clear_music", "update_setting"]),
      filename: z.string().trim().min(1).max(240).optional(),
      position: z.number().int().min(1).max(30).optional().describe("1-based insertion or move destination"),
      from_position: z.number().int().min(1).max(30).optional().describe("1-based source index for move_voice"),
      setting: z.enum(["project_name","music_level","after_intro_seconds","between_seconds","outro_seconds","music_under_intro","mute_music_during_final_voice","gentle_cleanup","normalize_voice","denoise_voice","export_stems","additional_instructions"]).optional(),
      value: z.union([z.string(), z.number(), z.boolean()]).optional()
    })
  }, async ({ project, action, filename, position, from_position, setting, value }) => {
    const next: Record<string, unknown> = { ...project, voice_files: [...project.voice_files] };
    const voices = next.voice_files as string[];
    if (action === "add_voice") {
      if (!filename) return projectError("Provide the voice filename to add.");
      if (voices.includes(filename)) return projectError("That voice filename is already in the project.");
      if (voices.length >= 30) return projectError("A chat plan supports up to 30 recording names.");
      voices.splice(Math.min(voices.length, (position ?? voices.length + 1) - 1), 0, filename);
    } else if (action === "remove_voice") {
      if (!filename) return projectError("Provide the voice filename to remove.");
      const index = voices.indexOf(filename);
      if (index < 0) return projectError("The given voice filename is not in the project.");
      voices.splice(index, 1);
    } else if (action === "move_voice") {
      const from = (from_position ?? 0) - 1, to = (position ?? 0) - 1;
      if (from < 0 || from >= voices.length || to < 0 || to >= voices.length)
        return projectError("Provide valid 1-based from_position and position.");
      const [item] = voices.splice(from, 1);
      voices.splice(to, 0, item);
    } else if (action === "set_music") {
      if (!filename) return projectError("Provide a music filename.");
      next.music_file = filename;
    } else if (action === "clear_music") {
      next.music_file = "";
    } else if (action === "update_setting") {
      if (!setting || value === undefined) return projectError("Provide setting and value.");
      next[setting] = value;
    }
    const parsed = projectSchema.safeParse(next);
    if (!parsed.success) return projectError("Invalid project edit: " + parsed.error.issues.map(i => i.message).join("; "));
    return projectAnswer(resultForProject(origin, parsed.data));
  });

  return server;
}

export default {
  async fetch(request: Request, env: WorkerEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      return Response.json({ name: "audio-studio", status: "ok", version: "2.1.0-preview", mcp: "/mcp", app: "/" },
        { headers: { "cache-control": "no-store" } });
    }
    if (url.pathname === "/mcp") {
      // One factory/handler per request avoids state shared across different users.
      return createMcpHandler(() => createServer(url.origin)).fetch(request);
    }
    return env.ASSETS.fetch(request);
  }
};
