#!/usr/bin/env python3

import argparse
import html
import json
import mimetypes
import posixpath
import sys
import re
import urllib.parse
import webbrowser
import threading
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

__author__ = "Quinten C"


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".avif",
    ".ico",
}


FAVICON = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\tpHYs\x00\x00.#\x00\x00.#\x01x\xa5?v\x00\x00\x00\xabIDAT8\xcbc\xfc:[\xe4?\x03%\x80\x12\x03@z\x99H\xd5\xf4\xff\xff\xbe\xff \x0c\xe3\xb3`S\xd4\xd0\xd0\xf0\x1f\x8b\x18#6\xb5Lx4\xa7#a\xb88#\xa3\x13#\x08\xe34\x00I3\x06\x1f\x9b\xcb\x98\xb0\xd8\x9eN\xa4\xa1x]@4 \xc5\x80\x99\x04\r\x80\x86\xf4L,\x8ag\xe2\x8a\t&<\xd1\x053h\xe6;\x8f*\x06\x10&9%&\\\xd3\x06\xd3y'~\xfd\x87a\xb2R\xe2$\x0b6\xb8\xd3\xd1\ra\x04\x99\xb204\x8a\xa8P\xbcq\xa3\x07\xce\xd6\xd0(a\x88_\xbd\x8c\xb4h\x04iB7\x8c\x91\x9c\xdcX\xa9\xfb\x0cL\xb7_\x96b\x00\x00\x97cR^\xde\xcd]\x9a\x00\x00\x00\x00IEND\xaeB`\x82"

def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS

def natural_sort_key(path: Path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]

def list_images(directory: Path) -> list[Path]:
    return sorted(
        [p for p in directory.iterdir() if is_image_file(p)],
        key=natural_sort_key,
    )


def make_image_url(filename: str) -> str:
    quoted = urllib.parse.quote(filename)
    return f"/files/{quoted}"


def build_gallery_page(directory: Path, image_files: list[Path]) -> str:
    cards = []
    lightbox_items = []

    for idx, image_path in enumerate(image_files):
        name = image_path.name
        url = make_image_url(name)
        safe_name = html.escape(name)

        cards.append(
            f"""
            <figure class="card">
              <button
                class="image-button"
                type="button"
                data-index="{idx}"
                aria-label="Open {safe_name}"
              >
                <img src="{url}" alt="{safe_name}" loading="lazy">
              </button>
              <figcaption class="filename">{safe_name}</figcaption>
            </figure>
            """.strip()
        )

        lightbox_items.append({"name": name, "url": url})

    gallery_html = "\n".join(cards) if cards else """
      <div class="empty-state">
        <p>No image files found in this directory.</p>
        <p class="muted">Supported extensions: .png, .jpg, .jpeg, .gif, .webp, .bmp, .svg, .avif</p>
      </div>
    """

    dir_name = html.escape(str(directory.resolve()))
    image_count = len(image_files)
    images_json = json.dumps(lightbox_items).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Image Gallery</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #ffffff;
      --panel: #f6f7f8;
      --panel-2: #fbfbfc;
      --text: #111111;
      --muted: #666666;
      --border: #dddddd;
      --shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
      --radius: 16px;
      --max-width: 1200px;
      --overlay: rgba(0, 0, 0, 0.78);
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f1115;
        --panel: #171a21;
        --panel-2: #1b1f27;
        --text: #f4f4f4;
        --muted: #a0a0a0;
        --border: #2a2f3a;
        --shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
        --overlay: rgba(0, 0, 0, 0.88);
      }}
    }}

    * {{
      box-sizing: border-box;
    }}

    html, body {{
      height: 100%;
    }}

    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}

    .container {{
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 24px;
    }}

    .topbar {{
      display: flex;
      gap: 16px;
      align-items: flex-start;
      justify-content: space-between;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }}

    .title-block h1 {{
      margin: 0 0 6px 0;
      font-size: 1.8rem;
      font-weight: 700;
    }}

    .meta {{
      margin: 0;
      color: var(--muted);
      word-break: break-all;
    }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    button {{
      appearance: none;
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 999px;
      cursor: pointer;
      font: inherit;
    }}

    button:hover {{
      filter: brightness(0.98);
    }}

    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 18px;
    }}

    .card {{
      margin: 0;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow);
    }}

    .image-button {{
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--border);
      border-radius: 0;
      padding: 16px;
      background: var(--panel-2);
      cursor: zoom-in;
    }}

    .image-button:focus-visible,
    .lightbox-button:focus-visible,
    .lightbox-close:focus-visible {{
      outline: 2px solid var(--text);
      outline-offset: 2px;
    }}

    .image-button img {{
      display: block;
      width: 100%;
      height: 240px;
      object-fit: contain;
      background: transparent;
    }}

    .filename {{
      padding: 12px 14px 14px 14px;
      font-size: 0.95rem;
      color: var(--muted);
      word-break: break-word;
    }}

    .hide-filenames .filename {{
      display: none;
    }}

    .empty-state {{
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      padding: 32px;
      background: var(--panel);
    }}

    .empty-state p {{
      margin: 0 0 8px 0;
    }}

    .muted {{
      color: var(--muted);
    }}

    .lightbox {{
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: var(--overlay);
      z-index: 1000;
      padding: 24px;
    }}

    .lightbox.open {{
      display: flex;
    }}

    .lightbox-inner {{
      position: relative;
      width: min(96vw, 1400px);
      height: min(92vh, 1000px);
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      grid-template-rows: auto minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
    }}

    .lightbox-top {{
      grid-column: 1 / 4;
      display: flex;
      justify-content: flex-end;
    }}

    .lightbox-close {{
      font-size: 1.1rem;
      min-width: 48px;
      min-height: 48px;
    }}

    .lightbox-button {{
      min-width: 52px;
      min-height: 52px;
      font-size: 1.4rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .lightbox-stage {{
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 0;
      min-height: 0;
      height: 100%;
      background: transparent;
      overflow: hidden;
    }}

    .lightbox-stage img {{
      max-width: 100%;
      max-height: 100%;
      width: auto;
      height: auto;
      object-fit: contain;
      display: block;
      border-radius: 10px;
      box-shadow: var(--shadow);
      background: transparent;
    }}

    .lightbox-caption {{
      grid-column: 1 / 4;
      text-align: center;
      color: #f0f0f0;
      font-size: 0.95rem;
      word-break: break-word;
    }}

    .lightbox-counter {{
      display: block;
      margin-top: 4px;
      opacity: 0.85;
      font-size: 0.88rem;
    }}

    @media (max-width: 700px) {{
      .container {{
        padding: 16px;
      }}

      .gallery {{
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 14px;
      }}

      .image-button img {{
        height: 180px;
      }}

      .lightbox {{
        padding: 12px;
      }}

      .lightbox-inner {{
        width: 100%;
        height: 100%;
        grid-template-columns: 44px minmax(0, 1fr) 44px;
        grid-template-rows: auto minmax(0, 1fr) auto;
      }}

      .lightbox-button {{
        min-width: 44px;
        min-height: 44px;
        padding: 0;
      }}
    }}
  </style>
</head>
<body>
  <main class="container">
    <header class="topbar">
      <div class="title-block">
        <h1>Image Gallery</h1>
        <p class="meta">{image_count} image{"s" if image_count != 1 else ""} in {dir_name}</p>
      </div>
      <div class="controls">
        <button id="toggle-names" type="button" aria-pressed="false">Hide filenames</button>
      </div>
    </header>

    <section id="gallery" class="gallery">
      {gallery_html}
    </section>
  </main>

  <div id="lightbox" class="lightbox" aria-hidden="true">
    <div class="lightbox-inner" role="dialog" aria-modal="true" aria-label="Image viewer">
      <div class="lightbox-top">
        <button id="lightbox-close" class="lightbox-close" type="button" aria-label="Close viewer">✕</button>
      </div>

      <button id="lightbox-prev" class="lightbox-button" type="button" aria-label="Previous image">‹</button>

      <div class="lightbox-stage">
        <img id="lightbox-image" alt="">
      </div>

      <button id="lightbox-next" class="lightbox-button" type="button" aria-label="Next image">›</button>

      <div id="lightbox-caption" class="lightbox-caption"></div>
    </div>
  </div>

  <script id="image-data" type="application/json">{images_json}</script>

  <script>
    (() => {{
      const button = document.getElementById("toggle-names");
      const gallery = document.getElementById("gallery");

      let filenamesVisible = true;

      button.addEventListener("click", () => {{
        filenamesVisible = !filenamesVisible;
        gallery.classList.toggle("hide-filenames", !filenamesVisible);
        button.textContent = filenamesVisible ? "Hide filenames" : "Show filenames";
        button.setAttribute("aria-pressed", String(!filenamesVisible));
      }});

      const images = JSON.parse(document.getElementById("image-data").textContent);
      const imageButtons = Array.from(document.querySelectorAll(".image-button"));

      const lightbox = document.getElementById("lightbox");
      const lightboxImage = document.getElementById("lightbox-image");
      const lightboxCaption = document.getElementById("lightbox-caption");
      const closeButton = document.getElementById("lightbox-close");
      const prevButton = document.getElementById("lightbox-prev");
      const nextButton = document.getElementById("lightbox-next");

      let currentIndex = 0;
      let lastFocusedElement = null;

      function hasImages() {{
        return images.length > 0;
      }}

      function updateLightbox() {{
        if (!hasImages()) {{
          return;
        }}

        const item = images[currentIndex];
        lightboxImage.src = item.url;
        lightboxImage.alt = item.name;
        lightboxCaption.innerHTML = `
          <div>${{escapeHtml(item.name)}}</div>
          <span class="lightbox-counter">${{currentIndex + 1}} / ${{images.length}}</span>
        `;
      }}

      function openLightbox(index) {{
        if (!hasImages()) {{
          return;
        }}

        currentIndex = index;
        lastFocusedElement = document.activeElement;
        updateLightbox();

        lightbox.classList.add("open");
        lightbox.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        closeButton.focus();
      }}

      function closeLightbox() {{
        lightbox.classList.remove("open");
        lightbox.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";

        lightboxImage.removeAttribute("src");
        lightboxImage.alt = "";

        if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {{
          lastFocusedElement.focus();
        }}
      }}

      function showNext() {{
        if (!hasImages()) {{
          return;
        }}
        currentIndex = (currentIndex + 1) % images.length;
        updateLightbox();
      }}

      function showPrev() {{
        if (!hasImages()) {{
          return;
        }}
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        updateLightbox();
      }}

      function showFirst() {{
        if (!hasImages()) {{
          return;
        }}
        currentIndex = 0;
        updateLightbox();
      }}

      function showLast() {{
        if (!hasImages()) {{
          return;
        }}
        currentIndex = images.length - 1;
        updateLightbox();
      }}

      function escapeHtml(value) {{
        return value
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }}

      imageButtons.forEach((imgButton) => {{
        imgButton.addEventListener("click", () => {{
          const index = Number(imgButton.dataset.index);
          openLightbox(index);
        }});
      }});

      closeButton.addEventListener("click", closeLightbox);
      prevButton.addEventListener("click", showPrev);
      nextButton.addEventListener("click", showNext);

      lightbox.addEventListener("click", (event) => {{
        if (event.target === lightbox) {{
          closeLightbox();
        }}
      }});

      document.addEventListener("keydown", (event) => {{
        if (!lightbox.classList.contains("open")) {{
          return;
        }}

        switch (event.key) {{
          case "Escape":
            event.preventDefault();
            closeLightbox();
            break;
          case "ArrowLeft":
            event.preventDefault();
            showPrev();
            break;
          case "ArrowRight":
            event.preventDefault();
            showNext();
            break;
          case "Home":
            event.preventDefault();
            showFirst();
            break;
          case "End":
            event.preventDefault();
            showLast();
            break;
        }}
      }});
    }})();
  </script>
</body>
</html>
"""


class ImageGalleryHandler(BaseHTTPRequestHandler):
    server_version = "ImageGalleryServer/1.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.serve_gallery()
            return

        if path.startswith("/files/"):
            self.serve_file(path[len("/files/"):])
            return

        if path == "/favicon.ico":
            self.serve_favicon()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def serve_gallery(self) -> None:
        image_files = list_images(self.server.directory)
        page = build_gallery_page(self.server.directory, image_files).encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def serve_file(self, encoded_name: str) -> None:
        filename = urllib.parse.unquote(encoded_name)

        safe_name = posixpath.normpath("/" + filename).lstrip("/")
        if not safe_name or "/" in safe_name:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid filename")
            return

        file_path = self.server.directory / safe_name

        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        if not is_image_file(file_path):
            self.send_error(HTTPStatus.FORBIDDEN, "Only image files are served")
            return

        ctype, _ = mimetypes.guess_type(str(file_path))
        if ctype is None:
            ctype = "application/octet-stream"

        try:
            file_size = file_path.stat().st_size
            with file_path.open("rb") as f:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except BrokenPipeError:
            pass

    def serve_favicon(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(FAVICON)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(FAVICON)

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(
            f"[{self.log_date_time_string()}] "
            f"{self.address_string()} "
            f"{format % args}\n"
        )

def create_server(host, start_port):
    port = start_port

    while True:
        try:
            server = ThreadingHTTPServer((host, port), ImageGalleryHandler)
            return server, port
        except OSError as e:
            # 98 = address already in use
            if e.errno != 98:
                raise
            port += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve a minimal image gallery for the current directory."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Address to bind to. Default: 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on. Default: 8000",
    )
    parser.add_argument(
        "--dir",
        default=".",
        help=f"Directory containing images (default: current directory, which is now {Path.cwd()})"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    directory = Path(args.dir).expanduser().resolve()

    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        return 1

    server, port = create_server(args.host, args.port)
    server.directory = directory
    url = f"http://{args.host}:{port}"

    print(f"Serving image gallery from: {directory}")
    print(f"Open: {url}")

    if args.host in ("127.0.0.1", "localhost"):
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
