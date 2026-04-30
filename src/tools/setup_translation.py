# Business Intelligence Agent
# Copyright (C) 2026  B. Vignesh Kumar (Bravetux) <ic19939@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Download Helsinki-NLP translation models. Run: python -m src.tools.setup_translation"""
from src.agents.translation_agent import SUPPORTED_PAIRS, _local_path


def download_pair(pair_key: str):
    from transformers import MarianTokenizer, MarianMTModel
    model_id = SUPPORTED_PAIRS[pair_key]
    local = _local_path(pair_key)
    if local.exists():
        print(f"  {pair_key}: already downloaded at {local}")
        return
    print(f"  Downloading {pair_key} ({model_id}) ...")
    tokenizer = MarianTokenizer.from_pretrained(model_id)
    model = MarianMTModel.from_pretrained(model_id)
    local.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(str(local))
    model.save_pretrained(str(local))
    print(f"  {pair_key}: saved to {local}")


def run():
    print("Available language pairs:")
    pairs = list(SUPPORTED_PAIRS.keys())
    for i, p in enumerate(pairs, 1):
        print(f"  {i}. {p}")
    raw = input("\nEnter pair numbers to download (comma-separated, e.g. 1,3,9): ").strip()
    selected = [pairs[int(x.strip()) - 1] for x in raw.split(",") if x.strip().isdigit()]
    if not selected:
        print("No pairs selected.")
        return
    for pair in selected:
        download_pair(pair)
    print("\nDone. Users can now select these target languages in Settings.")


if __name__ == "__main__":
    run()
