"""IPTC AI field emission.

Writes the IPTC ExtensionXMP fields that signal AI generation:
  * `digitalSourceType` = `trainedAlgorithmicMedia` or `compositeWithTrainedAlgorithmicMedia`
  * `aiGeneratedIndicator` = `1`
  * `digitalImageGUID` (mirrors the C2PA claim)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any


_XMP_TEMPLATE = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="stitchwork">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:iptcExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#">
      <iptcExt:DigitalSourceType>{source_type}</iptcExt:DigitalSourceType>
      <iptcExt:AIGeneratedIndicator>1</iptcExt:AIGeneratedIndicator>
      <iptcExt:DigitalImageGUID>{guid}</iptcExt:DigitalImageGUID>
      <dc:creator><rdf:Seq><rdf:li>{creator}</rdf:li></rdf:Seq></dc:creator>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def write_iptc_ai_fields(
    image_path: Path,
    *,
    source_type: str = "trainedAlgorithmicMedia",
    guid: str,
    creator: str = "stitchwork/0.1.0",
) -> Path:
    """Embed the XMP block, OR sidecar it if Pillow is unavailable.

    Returns the path of whatever artefact was produced (image OR `.xmp`).
    """
    block = _XMP_TEMPLATE.format(source_type=source_type, guid=guid, creator=creator)
    try:
        from PIL import Image  # type: ignore
        img = Image.open(image_path)
        # XMP injection is format-specific; for PNG we use the iTXt approach
        if image_path.suffix.lower() == ".png":
            try:
                from PIL.PngImagePlugin import PngInfo  # type: ignore
                info = PngInfo()
                info.add_text("XML:com.adobe.xmp", block)
                img.save(image_path, pnginfo=info)
                return image_path
            except Exception:
                pass
    except ImportError:
        pass
    # Fallback — sidecar
    sidecar = image_path.with_suffix(image_path.suffix + ".xmp")
    sidecar.write_text(block, encoding="utf-8")
    return sidecar
