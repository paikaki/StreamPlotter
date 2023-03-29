import flask
import flask_restx
import sys
import threading
import uuid
from .__init__ import Figure as _Figure
from .__init__ import Axes as _Axes
from .__init__ import Line2D as _Line2D
from .__init__ import StreamPlotter as _StreamPlotter


TITLE = "StreamPlotter"
VERSION = "0.0"

_App: flask.Flask = flask.Flask(TITLE)
_Api: flask_restx.Api = flask_restx.Api(_App, version=VERSION, title=TITLE)
_Namespace = _Api.namespace("figure", description="Figure operations")
_Plotter: _StreamPlotter = _StreamPlotter(TITLE)


class Model:
    _Axes = _Api.model("Axes", {
        "title": flask_restx.fields.String(description="グラフタイトル", default="Title"),
        "unit": flask_restx.fields.String(description="単位", default="mm"),
        "seconds": flask_restx.fields.Integer(description="期間(秒)", default=600),
        "bottom": flask_restx.fields.Float(description="上限 (自動: null)", default=-100),
        "top": flask_restx.fields.Float(description="下限 (自動: null)", default=100)
    })
    _Line2D = _Api.model("Line2D", {
        "label": flask_restx.fields.String(description="データラベル", default="Label"),
        "interval": flask_restx.fields.Integer(description="間隔(秒)", default=1)
    })
    _DataStream = _Api.model("DataStream", {
        "value": flask_restx.fields.Float(description="プロットデータ", default=0),
        "clear": flask_restx.fields.Boolean(description="初期化フラグ", default=False)
    })


@_Namespace.route("/")
class Figure(flask_restx.Resource):

    @_Api.doc(description="すべてのプロットエリアを取得します。", responses={200: "Success"})
    def get(self):
        # **************************************************
        #   Process:
        # **************************************************
        list_ = list()
        for axes in _Plotter.figure.axes:
            axes = _Axes(axes)
            dict_ = {
                "id": str(axes.id),
                "title": axes.title,
                "unit": axes.unit,
                "seconds": axes.seconds,
                "bottom": axes.bottom,
                "top": axes.top
            }
            list_.append(dict_)
        response = {"axes": list_}
        return response, 200

    @_Api.doc(description="プロットエリアを追加します。", body=Model._Axes, responses={201: "Created", 400: "Bad Request"})
    def post(self):
        # **************************************************
        #   Validate:
        # **************************************************
        body = flask.request.json
        title = body.get("title")
        unit = body.get("unit")
        seconds = body.get("seconds", 100)
        if seconds < 1:
            response = {"message": "Bad Request"}
            return response, 400
        bottom = body.get("bottom")
        top = body.get("top")
        if (bottom is not None) and (top is not None) and (bottom > top):
            response = {"message": "Bad Request"}
            return response, 400
        # **************************************************
        #   Process:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        axes = figure.append(title)
        axes.entity.set_ylabel(unit)
        axes.set_xrange(seconds)
        axes.set_yrange(bottom, top)
        response = {
            "id": str(axes.id),
            "title": axes.title,
            "unit": axes.unit,
            "seconds": axes.seconds,
            "bottom": axes.bottom,
            "top": axes.top
        }
        return response, 201


@_Namespace.route("/<axes>")
class Axes(flask_restx.Resource):

    @_Api.doc(description="すべてのデータ系列を取得します。", responses={200: "Success", 400: "Bad Request", 404: "Not Found"})
    def get(self, axes):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        # **************************************************
        #   Process:
        # **************************************************
        list_ = list()
        for line in axes.entity.lines:
            line = _Line2D(line)
            dict_ = {
                "id": str(line.id),
                "label": line.label,
                "interval": line.interval
            }
            list_.append(dict_)
        response = {"lines": list_}
        return response, 200

    @_Api.doc(description="データ系列を追加します。", body=Model._Line2D, responses={201: "Created", 400: "Bad Request", 404: "Not Found"})
    def post(self, axes):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        body = flask.request.json
        label = body.get("label")
        interval = body.get("interval", 1)
        if interval < 1:
            response = {"message": "Bad Request"}
            return response, 400
        # **************************************************
        #   Process:
        # **************************************************
        line = axes.append(label)
        line.data.interval = interval
        response = {
            "id": str(line.id),
            "label": line.label,
            "interval": line.interval
        }
        return response, 201

    @_Api.doc(description="プロットエリアを更新します。", body=Model._Axes, responses={200: "Success", 400: "Bad Request", 404: "Not Found"})
    def put(self, axes):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        body = flask.request.json
        title = body.get("title", axes.title)
        unit = body.get("unit", axes.unit)
        seconds = body.get("seconds", axes.seconds)
        if seconds < 1:
            response = {"message": "Bad Request"}
            return response, 400
        bottom = body.get("bottom", axes.bottom)
        top = body.get("top", axes.top)
        if (bottom is not None) and (top is not None) and (bottom > top):
            response = {"message": "Bad Request"}
            return response, 400
        # **************************************************
        #   Process:
        # **************************************************
        axes.entity.set_title(title)
        axes.entity.set_ylabel(unit)
        axes.set_xrange(seconds)
        axes.set_yrange(bottom, top)
        response = {
            "id": str(axes.id),
            "title": axes.title,
            "unit": axes.unit,
            "seconds": axes.seconds,
            "bottom": axes.bottom,
            "top": axes.top
        }
        return response, 200

    @_Api.doc(description="プロットエリアを削除します。", responses={204: "No Content", 400: "Bad Request", 404: "Not Found"})
    def delete(self, axes):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        # **************************************************
        #   Process:
        # **************************************************
        figure.remove(axes.id)
        response = {"message": "No Content"}
        return response, 204


@_Namespace.route("/<axes>/<line>")
class Line2D(flask_restx.Resource):

    @_Api.doc(description="プロットデータを追加します。", body=Model._DataStream, responses={201: "Created", 400: "Bad Request", 404: "Not Found"})
    def post(self, axes, line):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        try:
            line = uuid.UUID(line)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        line = axes.extract(line)
        if line is None:
            response = {"message": "Not Found"}
            return response, 404
        body = flask.request.json
        value = body.get("value", None)
        clear = body.get("clear", False)
        # **************************************************
        #   Process:
        # **************************************************
        if clear:
            line.data.clear()
        line.data.append(value)
        response = {"message": "Created"}
        return response, 201

    @_Api.doc(description="データ系列を更新します。", body=Model._Line2D, responses={200: "Success", 400: "Bad Request", 404: "Not Found"})
    def put(self, axes, line):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        try:
            line = uuid.UUID(line)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        line = axes.extract(line)
        if line is None:
            response = {"message": "Not Found"}
            return response, 404
        body = flask.request.json
        label = body.get("label", line.label)
        interval = body.get("interval", line.interval)
        if interval < 1:
            response = {"message": "Bad Request"}
            return response, 400
        # **************************************************
        #   Process:
        # **************************************************
        line.entity.set_label(label)
        line.entity.axes.legend()
        line.data.interval = interval
        response = {
            "id": str(line.id),
            "label": line.label,
            "interval": line.interval
        }
        return response, 200

    @_Api.doc(description="データ系列を削除します。", responses={200: "No Content", 400: "Bad Request", 404: "Not Found"})
    def delete(self, axes, line):
        # **************************************************
        #   Validate:
        # **************************************************
        figure = _Figure(_Plotter.figure)
        try:
            axes = uuid.UUID(axes)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        axes = figure.extract(axes)
        if axes is None:
            response = {"message": "Not Found"}
            return response, 404
        try:
            line = uuid.UUID(line)
        except:
            response = {"message": "Bad Request"}
            return response, 400
        line = axes.extract(line)
        if line is None:
            response = {"message": "Not Found"}
            return response, 404
        # **************************************************
        #   Process:
        # **************************************************
        axes.remove(line.id)
        response = {"message": "No Content"}
        return response, 204


if __name__ == "__main__":
    kwargs = dict()
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        kwargs["port"] = port
    _App.config["JSON_AS_ASCII"] = False
    thread = threading.Thread(target=_App.run, kwargs=kwargs, daemon=True)
    thread.start()
    _Plotter.run()(_Plotter.update)()
