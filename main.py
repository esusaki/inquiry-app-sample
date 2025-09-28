
import logging
import os
import json
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from contextlib import asynccontextmanager
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
CONFIG_FILE = "config.json"

# --- Global Config ---
# 設定ファイルから読み込んだ設定を保持します。
config = {
    "search_columns": []
}
# ----------------------

# --- In-memory Cache ---
# アプリケーションのパフォーマンス向上のため、読み込んだデータとTF-IDFモデルをメモリにキャッシュします。
# 新しいファイルがアップロードされると、このキャッシュはクリアされます。
cache = {
    "filepath": None, # キャッシュされたファイルのパス
    "df": None,       # pandasデータフレーム
    "vectorizer": None, # TfidfVectorizerオブジェクト
    "matrix": None      # TF-IDFマトリクス
}
# ----------------------

def load_config():
    '''
    設定ファイル(config.json)を読み込み、グローバル変数configに格納します。
    '''
    global config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Successfully loaded config from {CONFIG_FILE}")
    except FileNotFoundError:
        logger.error(f"Config file not found at {CONFIG_FILE}. Using default empty config.")
        # config.jsonがない場合はデフォルト値（空）で続行
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {CONFIG_FILE}. Using default empty config.")
        # JSONの解析に失敗した場合もデフォルト値で続行

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Application startup...")
    load_config() # 設定ファイルの読み込み
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    # Clean up the uploads directory on startup
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    logger.info(f"Cleaned up {UPLOAD_DIR} directory.")
    yield
    # Shutdown event
    logger.info("Application shutdown...")

app = FastAPI(
    title="Inquiry Analysis App",
    description="An application to search and analyze inquiry tickets.",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

def _ensure_data_is_cached():
    """
    データがキャッシュされていることを確認し、キャッシュされていない、または古い場合はデータをロードします。
    """
    global cache
    logger.info("[_ensure_data_is_cached:start] Checking cache status.")
    
    try:
        files = os.listdir(UPLOAD_DIR)
        if not files:
            logger.warn("[_ensure_data_is_cached:warn] No files in uploads directory. Skipping cache load.")
            return

        latest_file = max([os.path.join(UPLOAD_DIR, f) for f in files], key=os.path.getctime)

        # キャッシュが最新であるか確認
        if cache["filepath"] == latest_file and cache["df"] is not None:
            logger.info("[_ensure_data_is_cached:success] Cache is up to date.")
            return

        logger.info(f"[_ensure_data_is_cached:info] Cache is stale or empty. Loading data from {latest_file}.")
        
        # --- ここから重い処理 ---
        df = pd.read_excel(latest_file)
        print("Excelの列名:", df.columns.tolist()) # デバッグ用に列名を出力
        df.fillna("", inplace=True)

        #print("重い処理 開始....")

        search_columns = config.get("search_columns", [])
        if not search_columns:
            raise HTTPException(status_code=500, detail="設定ファイルに検索対象列が指定されていません。")

        for col in search_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f'設定ファイルで指定された列 "{col}" がアップロードされたファイルに見つかりません。')

        df["search_text"] = df[search_columns].apply(lambda x: ' '.join(x.astype(str)), axis=1)

        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
        matrix = vectorizer.fit_transform(df["search_text"])
        # --- 重い処理ここまで ---

        # グローバルキャッシュを更新
        cache["filepath"] = latest_file
        cache["df"] = df
        cache["vectorizer"] = vectorizer
        cache["matrix"] = matrix
        
        logger.info("[_ensure_data_is_cached:success] Data loaded and cached successfully.")

    except Exception as e:
        logger.error(f"[_ensure_data_is_cached:error] Failed to load or cache data: {e}")
        # Invalidate cache on error
        cache = {"filepath": None, "df": None, "vectorizer": None, "matrix": None}
        # HTTPExceptionはそのままraiseする
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"データの読み込みまたはキャッシュ中に予期せぬエラーが発生しました: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("Root endpoint accessed. Serving index.html.")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global cache
    upload_path = os.path.join(UPLOAD_DIR, file.filename)
    logger.info(f"[upload_file:start] Uploading file: {file.filename}")
    try:
        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # ファイルが正常にアップロードされた後、キャッシュを無効化
        cache = {"filepath": None, "df": None, "vectorizer": None, "matrix": None}
        logger.info("[upload_file:success] Cache invalidated due to new file upload.")
        
        logger.info(f"[upload_file:success] File saved at: {upload_path}")
        return {"message": f"{file.filename} のアップロードが成功しました。"}
    except Exception as e:
        logger.error(f"[upload_file:error] Could not save file: {e}")
        raise HTTPException(status_code=500, detail="ファイルのアップロード中にエラーが発生しました。")

@app.get("/api/functional-areas")
async def get_functional_areas():
    logger.info("[get_functional_areas:start] Fetching functional areas.")
    if not os.listdir(UPLOAD_DIR):
        return []
    
    _ensure_data_is_cached() # データがキャッシュされていることを確認
    
    df = cache["df"]
    if df is None or "画面名称" not in df.columns:
        logger.error("[get_functional_areas:error] '画面名称' column not found in the cached dataframe.")
        raise HTTPException(status_code=400, detail="'画面名称'列がファイルに見つかりません。")
        
    functional_areas = df["画面名称"].dropna().unique().tolist()
    #logger.info(f"[get_functional_areas:success] Found functional areas: {functional_areas}")
    return functional_areas

@app.get("/api/search")
async def search_inquiries(keywords: str, functional_area: str = None):
    logger.info(f"[search_inquiries:start] Searching for '{keywords}' in '{functional_area}'")
    if not os.listdir(UPLOAD_DIR):
        raise HTTPException(status_code=400, detail="ファイルをアップロードしてください。")

    _ensure_data_is_cached() # データがキャッシュされていることを確認

    df = cache["df"]
    vectorizer = cache["vectorizer"]
    matrix = cache["matrix"]

    if df is None:
        raise HTTPException(status_code=500, detail="データがキャッシュされていません。")

    # 画面名称でフィルタリング
    target_df = df.copy()
    if functional_area and functional_area != "すべて":
        if "画面名称" in target_df.columns:
            target_df = target_df[target_df["画面名称"] == functional_area]
        else:
            raise HTTPException(status_code=400, detail="'画面名称'列が見つかりません。")

    if target_df.empty:
        logger.info("[search_inquiries:info] No data matches the filter.")
        return []

    # フィルタリングされた行のインデックスを取得
    filtered_indices = target_df.index.tolist()
    
    # 全体のTF-IDFマトリクスから、フィルタリングされた行に対応する部分をスライス
    filtered_matrix = matrix[filtered_indices]

    # 検索クエリをベクトル化
    query_vec = vectorizer.transform([keywords])

    # 類似度を計算
    cosine_similarities = cosine_similarity(query_vec, filtered_matrix).flatten()

    # 結果をデータフレームに追加
    target_df["similarity"] = cosine_similarities

    # 類似度でソート
    results_df = target_df.sort_values(by="similarity", ascending=False).head(100)

    results = results_df.to_dict(orient="records")
    logger.info(f"[search_inquiries:success] Found {len(results)} results.")
    return results

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server directly.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
