# First Light

Requires the file constring.py that includes a string named con_string that contains the connection string to the ZTF database.

Container is built using PodMan on NAU ITS servers. Building containers on other systems may require adjustment to the Containerfile.

To Run Locally:

    python app.py

To Build Container:

    podman run --name appcontainer -d -p 9010:9010 appimage
