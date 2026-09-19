# Unraid container icon

`icon.svg` is the Sipeed logo provided by the repository owner. `icon.png` is a
256 × 256 transparent PNG rendered from that source for the Unraid Docker UI.
The logo belongs to Sipeed; it is not covered by this project's MIT license.
This community dashboard is not an official Sipeed product.

The logo is used only by the Unraid template, not by the dashboard page or favicon.
Unraid downloads container icons separately from Docker images.

For an existing container, edit it in Unraid's Docker page, enable **Advanced View**,
and set **Icon URL** to:

```text
https://raw.githubusercontent.com/WUZICANGJIE/nanokvm-dashboard/main/unraid/icon.png
```

Apply the template change using the GUI. Updating the image alone does not replace
an existing container's saved Icon URL.
