"""Tests for the web API endpoints."""
from fastapi.testclient import TestClient
from compiler.web.app import app

client = TestClient(app)

SIMPLE_PROGRAM = "int main() { int x = 2 + 3; print(x); return 0; }"
BAD_PROGRAM = "int main( { }"


class TestCompileEndpoint:
    def test_compile_success(self):
        resp = client.post("/api/compile", json={"source": SIMPLE_PROGRAM})
        assert resp.status_code == 200
        data = resp.json()
        assert "tokens" in data
        assert "ast" in data
        assert "symbols" in data
        assert "ir" in data
        assert "ir_text" in data
        assert len(data["tokens"]) > 0
        assert data["ast"]["type"] == "Program"

    def test_compile_returns_symbols(self):
        resp = client.post("/api/compile", json={"source": SIMPLE_PROGRAM})
        data = resp.json()
        names = [s["name"] for s in data["symbols"]]
        assert "x" in names

    def test_compile_error(self):
        resp = client.post("/api/compile", json={"source": BAD_PROGRAM})
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is True
        assert data["phase"] == "parser"
        assert "line" in data


class TestOptimizeEndpoint:
    def test_optimize_success(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": ["CF", "DCE"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "optimized_ir_text" in data
        assert "metrics" in data
        assert "diff" in data
        assert data["output_correct"] is True

    def test_optimize_all_passes(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": ["CF", "CP", "SR", "AS", "DCE", "CSE"]
        })
        data = resp.json()
        assert data["metrics"]["code_size"] > 0

    def test_optimize_empty_passes(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": []
        })
        data = resp.json()
        assert "optimized_ir_text" in data

    def test_optimize_invalid_pass(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": ["INVALID"]
        })
        data = resp.json()
        assert data["error"] is True
        assert data["phase"] == "optimization"


class TestExamplesEndpoint:
    def test_list_examples(self):
        resp = client.get("/api/examples")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8
        names = [e["name"] for e in data]
        assert "fibonacci" in names
        assert "factorial" in names

    def test_get_example(self):
        resp = client.get("/api/examples/fibonacci")
        assert resp.status_code == 200
        data = resp.json()
        assert "source" in data
        assert "int main()" in data["source"]

    def test_get_nonexistent_example(self):
        resp = client.get("/api/examples/nonexistent")
        assert resp.status_code == 404

    def test_get_example_rejects_traversal(self):
        resp = client.get("/api/examples/..%5c..%5creadme")
        assert resp.status_code == 404


class TestBenchmarkEndpoint:
    def test_benchmark(self):
        source = "int main() { int x = 2 + 3; print(x); return 0; }"
        resp = client.post("/api/benchmark", json={"source": source})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "baseline" in data
        assert len(data["results"]) > 1


class TestIndexPage:
    def test_serves_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_html_contains_key_elements(self):
        resp = client.get("/")
        html = resp.text
        assert 'id="learn-mode"' in html
        assert 'id="explore-mode"' in html
        assert "compile()" in html or "compile(" in html
        assert "Compiler Explorer" in html
