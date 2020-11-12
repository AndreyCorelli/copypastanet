from vizualization.folder_map import FolderNode
from vizualization.source_tree_render import SourceTreeRender


class HtmlSourceTreeRender(SourceTreeRender):
    def render(self):
        pass

    def render_folder_or_file(self, node: FolderNode):