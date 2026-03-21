import requests


def summarize(text):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen3.5:4b",
        "prompt": "要約してください。" + text,
        "stream": False
    }

    print("Summarizing with Ollama...")
    try:
        res = requests.post(url, json=data)
    except Exception as e:
        print(f"\nError connecting to Ollama: {e}")

    return res.json()["response"]


if __name__ == "__main__":
    result = summarize("""昔々、あるところに、おじいさんとおばあさんが住んでいました。おじいさんは山へ芝刈りに、おばあさんは川へ洗濯に行きました。おばあさんが川で洗濯をしていると、どんぶらこ、どんぶらこと大きな桃が流れてきました。おばあさんはその桃を拾って家に持ち帰り、割ってみると、中から元気な男の子が出てきました。この男の子が桃太郎です。桃太郎はすくすくと育ち、やがて鬼ヶ島へ鬼退治に行くことを決意しました。おばあさんは桃太郎のためにきびだんごを作り、桃太郎は旅に出ました。道中、桃太郎は犬、猿、雉を家来にし、力を合わせて鬼ヶ島へ向かいました。鬼ヶ島に着いた桃太郎たちは、鬼たちと激しい戦いを繰り広げ、見事に鬼を退治しました。そして、鬼が奪った宝物を持ち帰り、村人たちに分け与え、村は平和になりました。""")
    print(result)
