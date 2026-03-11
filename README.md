# Overview

Image Gallery Server is a small dependency-free Python program that starts a local web server and displays all images in the current directory in a clean and responsive gallery interface. It is intended for quick local browsing or sharing a folder of images without needing dependencies, external tools or frameworks. 

## Installation

```shell
wget https://raw.githubusercontent.com/tintin10q/simple-image-gallery/refs/heads/main/image_gallery_server.py
```

# Feature overview

- Serves all images in the current directory
- Minimal responsive image gallery
- Lightbox viewer for large images
- Keyboard navigation in the viewer
- Toggle button to show or hide filenames
- No JavaScript frameworks build step or external dependencies
- Simple HTTP server implemented using the Python standard library
- Display images in natural sorting order of filenames 

## Supported image formats

The following file extensions are recognized as images: png, jpg, jpeg, gif, webp, bmp, svg, ico and avif.
Other files are ignored.

If you want to add more image types just try to extend the `IMAGE_EXTENSIONS` set.

# Requirements

You only need python. I tested it and it even worked with 3.5.
No packages need to be installed.

# Usage

Run the server in the directory containing the images.

```shell
python image_gallery_server.py
```

By default the server runs on: `http://127.0.0.1:8000`. 

If it runs on `localhost` or `127.0.0.1` then the program will try to open the url in a browser using the standard [`webbrowser` module](https://docs.python.org/3/library/webbrowser.html).

If the specified port is not available, the program will search for a port that is available. 

## CLI options 

You can change the address, port and the directory.

```shell
python image_gallery_server.py --host 0.0.0.0 --port 8080 --dir ../some/other/directory 
```

# Security considerations

This server is designed for local use. It only serves image files from the current directory, but it does not implement authentication or HTTPS. Running it on a public network is therefore not recommended unless placed behind a reverse proxy and a firewal.

I tried to avoid path traversal attacks but use at your own risk!
