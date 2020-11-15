import os
from unittest import TestCase

from vizualization.html_source_tree_render import HtmlSourceTreeRender


class TestRenderSources(TestCase):
    def test_render(self):
        cur_folder = os.path.dirname(os.path.abspath(__file__))
        src_folder = os.path.join(cur_folder, 'code_folder')
        out_folder = os.path.join(cur_folder, 'rendered_folder')

        render = HtmlSourceTreeRender()
        render.explore_sources([src_folder], out_folder)
        render.render()
