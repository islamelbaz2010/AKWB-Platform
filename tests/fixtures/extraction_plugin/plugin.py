"""Sample extraction pipeline plugin fixture."""

from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.plugins import Reader


class PrefixStripReader(Reader):
    """Custom reader that strips a known prefix before normalization."""

    supported_mime_types = ("text/x-custom",)

    def read(self, artifact, content, context=None):
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        return NormalizedContent(
            kind=ContentKind.TEXT,
            mime_type=artifact.mime_type,
            content=text.removeprefix(".CUSTOM "),
            source_uri=artifact.relative_path or artifact.name,
        )


def register(api):
    """Register the custom reader with the plugin system."""
    api.register_port("reader", PrefixStripReader())
