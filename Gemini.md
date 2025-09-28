# Gemini CLI 開発ルール定義書

このドキュメントは、Gemini CLIを使用してVS Code上で開発を行う際のルールを定義したものです。

---

## 1. ログ出力処理の設置
- 各処理にログ出力を設けること。
- ログはエラー発生時にGenAIが修正箇所・方法を特定し、精度の高い対処ができる形式とする。
- ログタグは「クラス名:処理名」の形式で統一する。
  - 例: `[UserController:login]`, `[OrderService:validateOrder]`

---

## 2. 無償ソフトウェアのみ使用
- アプリは無償のソフトウェアおよびミドルウェアのみで動作するように設計すること。

---

## 3. テストコードの生成
- 実装コードに対して必ずテストコードを併せて生成すること。
- テストクラス名は対象クラス＋`Test`とする。
  - 例: `UserServiceTest`, `LoginControllerTest`
- テスト関数名は何をテストしているか明確にする。
  - 例: `shouldReturnUserWhenValidId`, `shouldThrowErrorOnInvalidLogin`

---

## 4. テスト仕様書の生成
- コード生成時に以下のテスト仕様書も併せて作成すること。
  - 単体テスト仕様書
  - 結合テスト仕様書
  - 総合テスト仕様書

---

## 5. 命名ルール（Vibe Coding用）

### 変数名・関数名
- キャメルケース（camelCase）を使用
  - 例: `userName`, `getUserInfo`, `calculateTotalPrice`
- 動詞＋名詞で関数名を構成
  - 例: `fetchUserData`, `updateProfile`, `sendEmail`
- 略語は避ける（例: `usrNm` → `userName`）

### クラス名・ファイル名
- パスカルケース（PascalCase）を使用
  - 例: `UserController`, `LoginService`, `ProductRepository`
- クラス名は役割が明確になるように
  - 例: `UserManager`, `OrderValidator`

### 定数名
- 全て大文字＋アンダースコア区切り
  - 例: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`

### パッケージ・フォルダ名
- Java: すべて小文字＋ドット区切り
  - 例: `com.vibecoding.user`, `com.vibecoding.utils`
- Python: スネークケース
  - 例: `user_service`, `data_utils`

### HTML/CSS/JSファイルの命名
- ファイル名は機能ベース＋役割
  - 例: `login_form.html`, `user_list.css`, `dashboard_chart.js`

### テストコード
- テストクラス名は対象クラス＋`Test`
  - 例: `UserServiceTest`, `LoginControllerTest`
- テスト関数名は何をテストしているか明確に
  - 例: `shouldReturnUserWhenValidId`, `shouldThrowErrorOnInvalidLogin`

### コメントについて
- 必ずコメントを日本語で入れて、処理の意味を丁寧に説明してください。　