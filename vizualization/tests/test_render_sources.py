import os
from unittest import TestCase

from vizualization.html_source_tree_render import HtmlSourceTreeRender


class TestRenderSources(TestCase):
    def test_render(self):
        cur_folder = os.path.dirname(os.path.abspath(__file__))
        src_folder = os.path.join(cur_folder, 'code_folder')
        out_folder = os.path.join(cur_folder, 'rendered_folder')

        #src_folder = '/home/andrey/sources/contraxsuite/lexpredict-contraxsuite-services/contraxsuite_services/apps'
        #out_folder = '/home/andrey/sources/contraxsuite/contraxsuite_serv_copypaste'

        render = HtmlSourceTreeRender()
        render.explore_sources([src_folder], out_folder, min_cps_len=2)
        render.render()
