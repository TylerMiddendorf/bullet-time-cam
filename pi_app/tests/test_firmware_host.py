import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class FirmwareHostTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("g++"), "g++ is required for the firmware host regression")
    def test_ack_identity_tokens_match_exact_numeric_values(self):
        repository = Path(__file__).resolve().parents[2]
        header_dir = repository / "button_capture"
        source = r"""
#include "metadata_match.h"

int main() {
  if (!metadataContainsExactToken("{\"capture_seq\":1}", "\"capture_seq\":1")) return 1;
  if (metadataContainsExactToken("{\"capture_seq\":10}", "\"capture_seq\":1")) return 2;
  if (metadataContainsExactToken("{\"boot_id\":1234}", "\"boot_id\":123")) return 3;
  if (!metadataContainsExactToken("{\"node_uid\":\"ABC\",\"capture_seq\":2}",
                                  "\"node_uid\":\"ABC\"")) return 4;
  return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp:
            temp_dir = Path(temp)
            source_path = temp_dir / "metadata_match_test.cpp"
            executable = temp_dir / "metadata_match_test.exe"
            source_path.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    f"-I{header_dir}",
                    str(source_path),
                    "-o",
                    str(executable),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
