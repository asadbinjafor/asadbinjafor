"""Check constraints that SVG path animation otherwise fails silently on."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import visual_map


class VisualMapTests(unittest.TestCase):
    def test_morph_targets_have_matching_topology_and_stay_inside_frame(self):
        shapes=visual_map.scenes()
        lengths=set()
        for name,data in shapes.items():
            with self.subTest(scene=name):
                marks=re.findall(r"M(\d+),(\d+)h(\d+)v1h-(\d+)Z",data)
                self.assertEqual("".join(f"M{x},{y}h{w}v1h-{back}Z" for x,y,w,back in marks),data)
                lengths.add(len(marks))
                self.assertGreater(len(marks),5000)
                for x,y,w,back in marks:
                    self.assertEqual(w,back)
                    self.assertLessEqual(int(x)+int(w),visual_map.WIDTH)
                    self.assertLess(int(y),visual_map.HEIGHT)
        self.assertEqual(len(lengths),1)

    def test_motion_has_an_independent_static_portrait_fallback(self):
        import xml.etree.ElementTree as ET
        root=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+visual_map.render(0,0,400,492)+'</svg>')
        ns={"svg":"http://www.w3.org/2000/svg"}
        fallback=root.find('.//svg:path[@class="map-still"]',ns)
        motion=root.find('.//svg:path[@class="map-motion"]/svg:animate',ns)
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback.get("d"),visual_map.scenes()["portrait"])
        self.assertEqual(len(motion.get("values").split(";")),len(motion.get("keyTimes").split(";")))
        self.assertIn("prefers-reduced-motion:reduce",visual_map.MOTION_CSS)


if __name__=="__main__":
    unittest.main()
