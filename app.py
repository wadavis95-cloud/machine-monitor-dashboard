from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, render_template

from loader import load_data
from replayer import EngineReplayer


def create_app():
    app = Flask(__name__, static_folder=None)
    data = load_data(Path(__file__).parent / "data" / "train_FD001.txt")
    engine_1_final_cycle = int(data.loc[data["unit"] == 1, "cycle"].max())
    reference = data.loc[(data["unit"] != 1) & (data["cycle"].between(1, 30)), "s_2"]
    lower, upper = reference.quantile([0.05, 0.95])
    t24_band = {"lower": float(lower), "upper": float(upper)}
    replayers = {}
    playback_lock = Lock()

    @app.get("/")
    def dashboard():
        return render_template(
            "index.html", final_cycle=engine_1_final_cycle, t24_band=t24_band
        )

    @app.get("/api/engine/<int:unit>/next")
    def next_reading(unit):
        with playback_lock:
            if unit not in replayers:
                replayers[unit] = EngineReplayer(data, unit)
            row = replayers[unit].next()

        return jsonify(row if row is not None else {"done": True})

    return app
