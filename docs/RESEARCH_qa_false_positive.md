# Research: False-positive "Tài liệu không đề cập" trong Q&A (RAG)

> Worker: Research. Đầu vào cho: Prompt Engineering Worker (xem mục cuối).
> Phương pháp: đọc code thật → research học thuật/kỹ thuật/thực tế có trích dẫn.

## TL;DR
False positive "không đề cập" **chủ yếu là lỗi RETRIEVAL (recall), không chỉ do prompt**. Pipeline hiện tại chỉ lấy `top_k=5` bằng semantic search thuần, **không hybrid, không re-rank, không threshold**. LLM chỉ nhìn thấy 5 chunk; nếu chunk chứa đáp án không nằm trong 5 chunk đó, LLM **trung thực** báo "không đề cập" — và prompt strict biến trượt-retrieval thành lời từ chối. Việc cắt embedding 3072→768 dim **KHÔNG phải nguyên nhân** (chỉ mất 0.26% chất lượng). Quick win an toàn nhất: **nâng recall (tăng top_k + MMR + re-rank)** và **tinh chỉnh prompt phân biệt "chưa truy xuất được" vs "thực sự vắng mặt"** — cả hai đều giảm false positive mà KHÔNG nới lỏng chống hallucination.

---

## Root Cause Analysis (dựa trên code thật)

Pipeline Q&A: `qa_service.ask_stream_response` → `embed_query` → `chunk_repository.get_similar(..., top_k=5)` → `answer_question_stream` với prompt `_qa_prompt`.

### Nguyên nhân do RETRIEVAL (chính)
1. **top_k=5 quá thấp cho tài liệu dài.** `get_similar(query_embedding, doc_id, top_k=5)` ([chunk_repository.py](../backend/app/repositories/chunk_repository.py)). Tài liệu mẫu 52 trang / 17.845 từ → hàng trăm chunk 512-char. Lấy 5 chunk → recall thấp; nếu đáp án nằm ở chunk thứ 6+ theo cosine, LLM không bao giờ thấy nó. Pinecone & cộng đồng nhấn mạnh: *"nếu thông tin liên quan không có trong context ngay từ đầu, không re-rank hay model nào cứu được"* → biểu hiện đúng là **false refusal** ([Pinecone Rerankers](https://www.pinecone.io/learn/series/rag/rerankers/); [DEV: RAG Recall vs Precision](https://dev.to/optyxstack/rag-recall-vs-precision-a-practical-diagnostic-guide-for-reliable-retrieval-26oh)).
2. **Semantic thuần bỏ sót khớp từ khóa chính xác.** Embedding yếu với tên riêng/từ viết tắt/thuật ngữ hiếm (vd "Analytic Geometry", "Gram-Schmidt", "SVD"). BM25/full-text mạnh ở khớp literal. Hybrid bù nhau: Recall@5 hybrid+rerank **0.816** vs dense thuần **0.587** (+39%) ([arXiv 2604.01733](https://arxiv.org/html/2604.01733v1); [techbytes Hybrid RAG 2026](https://techbytes.app/posts/hybrid-rag-search-bm25-embeddings-deep-dive-2026/)).
3. **Không có re-rank.** 5 chunk theo cosine không đảm bảo là 5 chunk *trả lời được* câu hỏi. *"Cosine đo độ gần, không đo độ hữu ích; topic similarity ≠ answer capability"* ([DEV: Why Cosine Fails](https://dev.to/mossforge/why-cosine-similarity-fails-in-rag-and-what-to-use-instead-pb5); [Nick Berens: RAG Score Thresholds](https://nickberens.me/blog/understanding-rag-score-thresholds/)).

### Nguyên nhân do PROMPT (khuếch đại)
4. **Quy tắc từ chối quá cứng.** `_qa_prompt` ([gemini_service.py](../backend/app/services/gemini_service.py) dòng 491–503): *"Nếu chủ đề câu hỏi THỰC SỰ VẮNG MẶT trong toàn bộ ngữ cảnh → chỉ viết 'Tài liệu không đề cập đến điều này.'"* Vấn đề: prompt chỉ thấy 5 chunk, **không phân biệt được "vắng mặt thật" với "không nằm trong 5 chunk truy xuất"**. Ràng buộc "CHỈ VÀO ngữ cảnh" là đúng cho faithfulness, nhưng kết hợp recall thấp → từ chối sai. Đây chính là trade-off đã được định lượng: ép "answer only from context" giảm hallucination 30–50% nhưng làm tụt tỷ lệ trả lời (RAG từ chối khi context thiếu) ([Ragas, arXiv 2309.15217](https://arxiv.org/pdf/2309.15217); [Sufficient Context, arXiv 2411.06037](https://arxiv.org/pdf/2411.06037)).

### ĐÃ LOẠI TRỪ: embedding 768-dim
Cắt 3072→768 qua Matryoshka chỉ mất **0.26%** chất lượng (MTEB 67.99 vs 68.17) — **không phải nguyên nhân**, không cần đổi ([Google Developers Blog](https://developers.googleblog.com/gemini-embedding-available-gemini-api/)). Giữ nguyên 768.

---

## Bảng so sánh giải pháp

| Giải pháp | Giảm false-positive | Chi phí triển khai (LangChain+pgvector+Gemini) | Rủi ro hallucination/lan man & cách kiểm soát |
|---|---|---|---|
| **A. Tăng top_k (5→12–15)** | Trung bình–Cao (tăng recall trực tiếp) | **Rất thấp** — đổi 1 tham số `get_similar` | Thấp. Nhiều context có thể gây "lost in the middle"/lan man → kiểm soát bằng re-rank hoặc cap số chunk đưa vào prompt. |
| **B. MMR (Maximal Marginal Relevance)** | Trung bình (đa dạng chunk, tránh 5 chunk trùng ý) | Thấp — pgvector lấy top ~30 rồi MMR ở app, hoặc LangChain retriever | Thấp; giảm lan man vì bớt chunk trùng lặp ([MMR, Medium](https://medium.com/@celaguleiva/good-questions-lead-to-great-answers-metrics-for-using-rag-with-cosine-similarity-and-maximal-a7cdbcb15e54)). |
| **C. Hybrid search (vector + Postgres full-text/`tsvector` RRF)** | **Cao** | Trung bình — **không thêm hạ tầng**: pgvector + `tsvector`/`ts_rank` sẵn trong Postgres, fuse bằng RRF | Thấp; tăng recall của khớp từ khóa. RRF tránh phải chuẩn hóa điểm thủ công ([arXiv 2604.01733](https://arxiv.org/pdf/2604.01733)). |
| **D. Re-rank (cross-encoder)** | **Cao** (lấy top 50–100 → rerank → top 5–10) | Trung bình–Cao — Cohere Rerank API (~$1/1k, thêm dependency/secret) hoặc BGE-reranker local (thêm model) | Thấp–Trung bình; **giảm** lan man vì lọc chunk nhiễu. +12.1pp Recall@5, +120ms ([Pinecone](https://www.pinecone.io/learn/series/rag/rerankers/); [arXiv 2604.01733](https://arxiv.org/html/2604.01733v1)). |
| **E. Query rewriting / HyDE** | Trung bình–Cao (khớp ngữ nghĩa tốt hơn) | Trung bình — **thêm 1 lần gọi Gemini/câu hỏi** → tốn latency + quota (đụng NFR Q&A <10s và free-tier 429) | **Trung bình** — HyDE sinh "tài liệu giả" có thể lệch; phải embed câu trả lời giả để *retrieve*, KHÔNG đưa vào prompt sinh đáp án ([HyDE, arXiv 2212.10496](https://arxiv.org/abs/2212.10496)). |
| **F. Relevance/intent router** | Trung bình (chặn câu hỏi thật sự lạc đề sớm) | Trung bình — thêm 1 lần gọi phân loại | Trung bình — router sai lại tạo false-positive mới; chỉ nên dùng để định tuyến, không để từ chối cứng. |
| **G. Hard similarity threshold cutoff** | **Thấp / phản tác dụng** | Thấp | **CAO** — *"dịch threshold 0.1 biến trợ lý thành kẻ lan man"*; cosine ≠ khả năng trả lời. **Không khuyến nghị làm cơ chế từ chối chính** ([Nick Berens](https://nickberens.me/blog/understanding-rag-score-thresholds/); [Meisin Lee](https://meisinlee.medium.com/better-rag-retrieval-similarity-with-threshold-a6dbb535ef9e)). |
| **H. Sửa prompt (phân biệt "chưa truy xuất" vs "vắng mặt")** | Trung bình–Cao | **Rất thấp** | Thấp **nếu giữ nguyên rule grounding**. Giao cho Prompt Worker (mục dưới). |

---

## Khuyến nghị (ưu tiên theo ROI, hợp stack hiện tại)

**Giai đoạn 1 — Quick win (làm trước, không thêm dependency):**
1. **Tăng `top_k` 5 → 12–15** trong `get_similar` (recall lên ngay).
2. **Sửa prompt** theo hướng phân biệt "ngữ cảnh chưa đủ" vs "chủ đề thực sự ngoài tài liệu" + cho phép tổng hợp/suy luận trong phạm vi context (giữ nguyên cấm dùng kiến thức ngoài). → Prompt Worker.
3. (Tùy chọn rẻ) **MMR** để 12–15 chunk đa dạng, tránh trùng ý.

**Giai đoạn 2 — Nâng chất lượng retrieval (không thêm hạ tầng):**
4. **Hybrid search** = pgvector (semantic) + Postgres `tsvector`/`ts_rank` (lexical), fuse bằng **RRF**. Bù đúng điểm yếu "thuật ngữ/tên riêng" của tài liệu học thuật. Đây là đòn bẩy recall lớn nhất mà không cần dịch vụ ngoài.

**Giai đoạn 3 — Nếu vẫn còn false-positive (kiến trúc lớn):**
5. **Re-rank cross-encoder** (Cohere Rerank API hoặc BGE local): retrieve rộng (top 50–100 hybrid) → rerank → top 8–10 vào prompt. Vừa tăng recall hiệu dụng vừa giảm lan man.
6. HyDE / router: cân nhắc sau cùng vì tốn thêm lần gọi Gemini (đụng quota/NFR).

**KHÔNG nên:** dùng hard cosine-threshold làm cơ chế từ chối; đổi embedding dim.

> Lưu ý ràng buộc bất biến: các giải pháp A–F đều **không** nới lỏng chống hallucination — chúng đưa đúng chunk vào context để LLM **có cái mà grounded vào**, thay vì ép LLM đoán. Rule "chỉ dùng context, không bịa" giữ nguyên xuyên suốt.

---

## Action Items
- **[Backend]** `chunk_repository.get_similar`: nâng `top_k` 5→12–15 (GĐ1). Sau đó thêm hybrid `tsvector` + RRF (GĐ2). (Cần Backend Worker; không thuộc phạm vi research.)
- **[Prompt Eng]** Thiết kế 3 bản prompt strict/balanced/permissive theo định hướng dưới.
- **[Tester]** Cần bộ test case false-positive (câu hỏi CÓ liên quan bị từ chối) để đo trước/sau — hiện chưa có, **cần thêm data**.

---

## Dành riêng cho Prompt Engineering Worker

**Nguyên nhân gốc thuộc phần prompt** (`_qa_prompt`, gemini_service.py:491–503):
- Prompt coi "không thấy trong 5 chunk" = "vắng mặt trong tài liệu" → từ chối. Nhưng context chỉ là một lát cắt retrieval, không phải toàn tài liệu.
- Cụm từ chối là tuyệt đối ("THỰC SỰ VẮNG MẶT") nhưng không có nấc trung gian cho trường hợp "context có manh mối một phần / liên quan nhưng chưa đủ".

**Định hướng nới scope AN TOÀN (giữ baseline chống hallucination bất biến):**
1. **Baseline bất biến (cả 3 bản đều có):** chỉ dùng thông tin trong ngữ cảnh; cấm bổ sung kiến thức ngoài; cho phép *tổng hợp/suy luận từ chính ngữ cảnh* (đã là grounded).
2. **Phân biệt 3 trạng thái thay vì 2:** (a) trả lời được → trả lời; (b) ngữ cảnh có liên quan một phần → trả lời phần có căn cứ + nêu rõ phần nào tài liệu chưa nói; (c) chủ đề hoàn toàn ngoài tài liệu → câu từ chối. Điều này trực tiếp giảm false-positive ở nhóm (b) vốn đang bị gộp vào từ chối.
3. **Ranh giới "liên quan" rõ ràng** (chống mơ hồ gây false-positive): coi là liên quan nếu câu hỏi nhắm tới khái niệm/thuật ngữ/chủ đề xuất hiện trong ngữ cảnh, kể cả khi diễn đạt khác từ ngữ.
4. **3 mức:**
   - **strict**: chỉ trả lời khi căn cứ trực tiếp; (b) nghiêng về nêu thiếu.
   - **balanced** (đề xuất mặc định): cho phép tổng hợp + xử lý nhóm (b) bằng "trả lời phần có căn cứ".
   - **permissive**: tận dụng tối đa manh mối trong context, chỉ từ chối khi (c) — kèm cảnh báo rủi ro suy luận xa.
5. **Edge-case cần xử lý:** câu hỏi tổng quan ("nói về gì?"), câu hỏi đa phần (một phần có, một phần không), câu hỏi dùng từ đồng nghĩa/viết tắt khác tài liệu.
6. **Ví dụ bắt buộc:** ≥1 case từng false-positive — vd hỏi *"Analytic Geometry là gì?"* khi tài liệu có chương trình bày norms/inner product/orthogonality (liên quan) nhưng không định nghĩa literal cụm "Analytic Geometry" → bản cũ dễ từ chối; bản mới phải tổng hợp từ nội dung liên quan.

> **Quan trọng:** prompt KHÔNG tự sửa được false-positive do retrieval trượt (nhóm cần GĐ1–2). Prompt chỉ giải quyết phần nó gây ra (gộp nhóm (b) vào từ chối). Cần phối hợp với việc nâng top_k/hybrid để đạt mục tiêu.

---

## Nguồn
**Học thuật:** [HyDE arXiv:2212.10496](https://arxiv.org/abs/2212.10496) · [Ragas arXiv:2309.15217](https://arxiv.org/pdf/2309.15217) · [Sufficient Context arXiv:2411.06037](https://arxiv.org/pdf/2411.06037) · [BM25→Corrective RAG benchmark arXiv:2604.01733](https://arxiv.org/html/2604.01733v1)
**Kỹ thuật/uy tín:** [Pinecone — Rerankers & Two-Stage Retrieval](https://www.pinecone.io/learn/series/rag/rerankers/) · [Google Developers — Gemini Embedding GA](https://developers.googleblog.com/gemini-embedding-available-gemini-api/) · [Towards Data Science — Hybrid Search & Re-Ranking](https://towardsdatascience.com/hybrid-search-and-re-ranking-in-production-rag/)
**Thực tế/diễn đàn:** [DEV — RAG Recall vs Precision](https://dev.to/optyxstack/rag-recall-vs-precision-a-practical-diagnostic-guide-for-reliable-retrieval-26oh) · [DEV — Why Cosine Similarity Fails in RAG](https://dev.to/mossforge/why-cosine-similarity-fails-in-rag-and-what-to-use-instead-pb5) · [Nick Berens — RAG Score Thresholds](https://nickberens.me/blog/understanding-rag-score-thresholds/) · [techbytes — Hybrid RAG 2026](https://techbytes.app/posts/hybrid-rag-search-bm25-embeddings-deep-dive-2026/)
