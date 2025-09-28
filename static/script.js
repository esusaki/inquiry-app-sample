document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const functionalAreaSelect = document.getElementById('functional-area');
    
    // Search form elements
    const searchForm = document.getElementById('search-form');
    const keywordsInput = document.getElementById('keywords');
    const resultsContainer = document.getElementById('results-container');


    /**
     * バックエンドから機能名の一覧を取得し、ドロップダウンを更新する関数
     */
    async function updateFunctionalAreas() {
        console.log("機能名リストの更新を開始します...");
        try {
            // APIを呼び出して機能名リストを取得
            const response = await fetch('/api/functional-areas');

            // サーバーがエラーを返した場合（例：ファイルが見つからない）、そのエラーを処理する
            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ detail: '機能名の取得中に不明なエラーが発生しました。' }));
                throw new Error(errorResult.detail);
            }

            const areas = await response.json();

            // ドロップダウンの中身をいったんリセットするが、デフォルトの「すべて」オプションは維持する
            functionalAreaSelect.innerHTML = '<option value="">すべて</option>';

            // 取得した機能名リストの各項目に対して、新しいoption要素を作成して追加する
            areas.forEach(area => {
                const option = document.createElement('option');
                option.value = area;
                option.textContent = area;
                functionalAreaSelect.appendChild(option);
            });
            console.log("機能名リストの更新が成功しました。");

        } catch (error) {
            // エラーをコンソールに記録する。
            // ファイルアップロード自体は成功しているため、ユーザーの操作を妨げるようなエラー表示は行わない。
            console.error('機能名リストの更新エラー:', error.message);
        }
    }

    // ファイルアップロードフォームの送信イベントリスナーを追加
    uploadForm.addEventListener('submit', async (event) => {
        // デフォルトのページリreload動作をキャンセル
        event.preventDefault(); 

        const file = fileInput.files[0];
        if (!file) {
            uploadStatus.textContent = 'ファイルが選択されていません。';
            uploadStatus.className = 'status-error';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.textContent = 'アップロード中...';
        uploadStatus.className = 'status-info';

        try {
            // ファイルをバックエンドに送信
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                // アップロードが成功したら、成功メッセージを表示
                uploadStatus.textContent = result.message;
                uploadStatus.className = 'status-success';
                
                // そして、機能名ドロップダウンを更新する
                await updateFunctionalAreas();

            } else {
                // サーバーがエラーを返したら、エラーメッセージを表示
                uploadStatus.textContent = `エラー: ${result.detail || '不明なエラー'}`;
                uploadStatus.className = 'status-error';
            }
        } catch (error) {
            // fetch自体が失敗した場合（例：ネットワークエラー）、汎用的なエラーを表示
            console.error('アップロードエラー:', error);
            uploadStatus.textContent = 'アップロードに失敗しました。サーバーを確認してください。';
            uploadStatus.className = 'status-error';
        }
    });

    // 検索フォームの送信イベントリスナーを追加
    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // デフォルトのフォーム送信（ページリロード）を防止

        const keywords = keywordsInput.value;
        const functionalArea = functionalAreaSelect.value;

        if (!keywords.trim()) {
            resultsContainer.innerHTML = '<p class="status-error">検索キーワードを入力してください。</p>';
            return;
        }

        resultsContainer.innerHTML = '<p class="status-info">検索中...</p>';

        try {
            // URLSearchParamsを使用してクエリパラメータを安全にエンコード
            const params = new URLSearchParams({
                keywords: keywords,
                functional_area: functionalArea
            });

            const response = await fetch(`/api/search?${params.toString()}`);

            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ detail: '検索中に不明なエラーが発生しました。' }));
                throw new Error(errorResult.detail);
            }

            const results = await response.json();
            displayResults(results);

        } catch (error) {
            console.error('検索エラー:', error);
            resultsContainer.innerHTML = `<p class="status-error">検索に失敗しました: ${error.message}</p>`;
        }
    });

    /**
     * 検索結果をテーブル形式で表示する関数
     * @param {Array} results - バックエンドから返された検索結果の配列
     */
    function displayResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>該当する問い合わせは見つかりませんでした。</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'results-table';

        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>類似度</th>
                <th>ID</th>
                <th>タイトル</th>
                <th>機能名</th>
                <th>詳細</th>
            </tr>
        `;
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        results.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.similarity.toFixed(4)}</td>
                <td>${item.ID || ''}</td>
                <td>${item.タイトル || ''}</td>
                <td>${item.画面名称 || ''}</td>
                <td class="details-cell">${item.詳細 || ''}</td>
            `;
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        resultsContainer.innerHTML = ''; // コンテナをクリア
        resultsContainer.appendChild(table);
    }
});