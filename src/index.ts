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

function createServer(origin: string) {
  const server = new McpServer({ name: "audio-studio", version: "2.0.0-preview" });

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
      processing_note: "The browser preview currently exports settings and timeline, not rendered MP3."
    }) }] };
  });

  server.registerTool("get_audio_studio_defaults", {
    description: "Return supported default settings and audio-rendering limitations for Audio Studio. This tool does not access private files."
  }, async () => ({ content: [{ type: "text", text: JSON.stringify({
    defaults,
    accepted_audio_extensions: [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".mp4"],
    browser_form_url: origin + "/",
    mcp_version: "2.0.0-preview",
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

  return server;
}

export default {
  async fetch(request: Request, env: WorkerEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      return Response.json({ name: "audio-studio", status: "ok", version: "2.0.0-preview", mcp: "/mcp", app: "/" },
        { headers: { "cache-control": "no-store" } });
    }
    if (url.pathname === "/mcp") {
      // One factory/handler per request avoids state shared across different users.
      return createMcpHandler(() => createServer(url.origin))(request, env, ctx);
    }
    return env.ASSETS.fetch(request);
  }
};
