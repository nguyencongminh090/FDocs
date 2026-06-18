# Prompt Spec — Q&A 3 phiên bản giảm false-positive

> **Ngày**: 2026-06-18 | **Worker**: Prompt Engineering Worker
> **Model**: `gemini-2.5-flash` (thinking model — instruction-following tốt, cần rule cụ thể)
> **Input research**: [RESEARCH_qa_false_positive.md](RESEARCH_qa_false_positive.md)
> **Bối cảnh**: Backend GĐ1+GĐ2 đã xong (hybrid retrieval, top_k=12). LLM nhận nhiều context & đa dạng hơn → phần false-positive còn lại do prompt cần xử lý dứt điểm ở đây.
> **Output**: SPEC để Backend Worker áp vào `_qa_prompt` (gemini_service.py:491-503). Không sửa code trong tài liệu này.

---

## 1. Vấn đề prompt hiện tại

`_qa_prompt` (gemini_service.py:491-503) chỉ có **2 trạng thái**:
```
- Nếu câu trả lời rút ra được từ ngữ cảnh → trả lời.
- Nếu chủ đề câu hỏi THỰC SỰ VẮNG MẶT trong toàn bộ ngữ cảnh → "Tài liệu không đề cập đến điều này."
```
**Lỗi:** thiếu nấc trung gian. Câu hỏi mà ngữ cảnh **liên quan một phần** (có thuật ngữ/khái niệm gần, nhưng không khớp literal) bị model gộp vào nhánh "vắng mặt" → từ chối sai. Cụm `THỰC SỰ VẮNG MẶT` tuyệt đối khiến model dễ chọn từ chối khi không thấy khớp chính xác.

Dòng GROUNDING trong `_SYSTEM_TEXT` (dòng 39) cũng lặp lại logic nhị phân này → cần đồng bộ.

---

## 2. Baseline BẤT BIẾN (cả 3 bản giữ nguyên — KHÔNG đánh đổi)

1. Chỉ dùng thông tin trong **ngữ cảnh được cung cấp**; CẤM bổ sung kiến thức ngoài.
2. **Tổng hợp/suy luận từ chính ngữ cảnh là hợp lệ** (vẫn grounded).
3. Giới hạn độ dài giữ nguyên: tối đa 3–4 đoạn ngắn; câu đơn giản 1–2 câu. Không lan man, không lạc trọng tâm.
4. Trả lời cùng ngôn ngữ câu hỏi; giữ nguyên phần NGÔN NGỮ / ĐỊNH DẠNG / PHONG CÁCH của `_SYSTEM_TEXT`.

**Cơ chế chống hallucination = (1)+(2): model chỉ được nói cái có trong context.** 3 bản dưới đây chỉ thay đổi *ranh giới khi nào từ chối*, KHÔNG nới quyền dùng kiến thức ngoài. Đây là điểm mấu chốt để giảm false-positive mà không tăng hallucination.

---

## 3. Logic 3 trạng thái (thay cho 2)

| Trạng thái | Điều kiện | Hành vi |
|---|---|---|
| (a) Trả lời được | Ngữ cảnh chứa căn cứ trực tiếp hoặc tổng hợp được | Trả lời súc tích, **bold** chứng cứ |
| (b) Liên quan một phần | Ngữ cảnh nói về khái niệm/thuật ngữ/chủ đề mà câu hỏi nhắm tới, nhưng không phủ đủ | **Trả lời phần có căn cứ** + nêu rõ phần tài liệu chưa đề cập |
| (c) Hoàn toàn ngoài tài liệu | Không có bất kỳ khái niệm/thuật ngữ/chủ đề liên quan trong ngữ cảnh | Câu từ chối: "Tài liệu không đề cập đến điều này." |

**Ranh giới "liên quan" (chống mơ hồ):** coi là liên quan nếu câu hỏi nhắm tới khái niệm/thuật ngữ/chủ đề **xuất hiện trong ngữ cảnh, kể cả khi diễn đạt hoặc từ ngữ khác** (đồng nghĩa, viết tắt, tên gọi học thuật khác). False-positive cũ chủ yếu nằm ở nhóm (b) bị đẩy nhầm sang (c).

---

## 4. Ba phiên bản `_qa_prompt` (exact text)

> Phần `Ngữ cảnh:\n{context}` và `Câu hỏi: {question}` + `_lang_directive(lang)` ở cuối giữ nguyên như hiện tại. Dưới đây là phần **quy tắc** thay cho khối "Quy tắc bắt buộc" hiện hành.

### 4A. STRICT

```
Trả lời câu hỏi dựa CHỈ VÀO ngữ cảnh được cung cấp dưới đây.
Trả lời bằng cùng ngôn ngữ với câu hỏi.

Quy tắc bắt buộc:
- Chỉ dùng thông tin có trong ngữ cảnh. KHÔNG bổ sung kiến thức bên ngoài. Tổng hợp từ chính ngữ cảnh là hợp lệ.
- Nếu ngữ cảnh có căn cứ TRỰC TIẾP cho câu hỏi: trả lời súc tích, dùng **bold** cho phần chứng cứ quan trọng.
- Nếu ngữ cảnh chỉ liên quan MỘT PHẦN (có nhắc khái niệm/thuật ngữ câu hỏi nhắm tới nhưng không đủ căn cứ trực tiếp): trả lời đúng phần có căn cứ, rồi nêu rõ phần tài liệu không trình bày. Không suy diễn thêm.
- Chỉ khi ngữ cảnh KHÔNG chứa bất kỳ khái niệm, thuật ngữ hay chủ đề nào liên quan đến câu hỏi: viết đúng cụm "Tài liệu không đề cập đến điều này."
- Câu hỏi tổng quan ("nói về gì?", "chủ đề là gì?", "tóm tắt nội dung?"): tổng hợp từ các đoạn ngữ cảnh — đây là grounding hợp lệ.
- Độ dài: tối đa 3–4 đoạn ngắn; câu trả lời đơn giản thì 1–2 câu là đủ.
```

### 4B. BALANCED  ★ ĐỀ XUẤT MẶC ĐỊNH

```
Trả lời câu hỏi dựa trên ngữ cảnh được cung cấp dưới đây.
Trả lời bằng cùng ngôn ngữ với câu hỏi.

Quy tắc bắt buộc:
- Chỉ dùng thông tin có trong ngữ cảnh. KHÔNG bổ sung kiến thức bên ngoài. Được phép TỔNG HỢP và SUY LUẬN từ chính ngữ cảnh — đây vẫn là grounded.
- Nếu câu trả lời rút ra được từ ngữ cảnh (trực tiếp hoặc bằng tổng hợp): trả lời trực tiếp, súc tích. Dùng **bold** cho phần chứng cứ quan trọng.
- Nếu ngữ cảnh LIÊN QUAN câu hỏi nhưng chỉ phủ một phần: trả lời đầy đủ phần có căn cứ trong tài liệu, rồi nêu ngắn gọn phần nào tài liệu chưa đề cập. KHÔNG từ chối toàn bộ chỉ vì thiếu một phần.
- Một câu hỏi được coi là LIÊN QUAN nếu ngữ cảnh có nhắc tới khái niệm, thuật ngữ hoặc chủ đề mà câu hỏi nhắm tới — kể cả khi dùng từ ngữ, tên gọi hoặc viết tắt khác với câu hỏi.
- Câu hỏi tổng quan ("nói về gì?", "chủ đề là gì?", "tóm tắt nội dung?"): tổng hợp từ các đoạn ngữ cảnh.
- CHỈ khi ngữ cảnh hoàn toàn không chứa khái niệm, thuật ngữ hay chủ đề nào liên quan: viết đúng cụm "Tài liệu không đề cập đến điều này." Không dùng câu này khi ngữ cảnh có nội dung liên quan dù chỉ một phần.
- Độ dài: tối đa 3–4 đoạn ngắn; câu trả lời đơn giản thì 1–2 câu là đủ.
```

### 4C. PERMISSIVE

```
Trả lời câu hỏi dựa trên ngữ cảnh được cung cấp dưới đây.
Trả lời bằng cùng ngôn ngữ với câu hỏi.

Quy tắc bắt buộc:
- Chỉ dùng thông tin có trong ngữ cảnh. KHÔNG bổ sung kiến thức bên ngoài. Được phép tổng hợp và suy luận từ ngữ cảnh, kể cả nối nhiều đoạn lại với nhau.
- Tận dụng tối đa mọi manh mối liên quan trong ngữ cảnh để trả lời. Nếu phải suy luận xa, nêu rõ đó là suy luận từ nội dung tài liệu (vd: "Dựa trên phần trình bày về ..., có thể hiểu rằng ...").
- Nếu ngữ cảnh liên quan một phần: trả lời phần có căn cứ và nêu rõ phần còn thiếu. Ưu tiên cung cấp giá trị cho người đọc thay vì từ chối.
- CHỈ từ chối khi ngữ cảnh hoàn toàn không có khái niệm/thuật ngữ/chủ đề nào liên quan đến câu hỏi — khi đó viết đúng cụm "Tài liệu không đề cập đến điều này."
- Câu hỏi tổng quan: tổng hợp từ toàn bộ ngữ cảnh.
- Độ dài: tối đa 3–4 đoạn ngắn; câu đơn giản 1–2 câu.
```

### Đồng bộ dòng GROUNDING trong `_SYSTEM_TEXT` (áp cho cả 3 bản)
Thay dòng 39 hiện tại bằng:
```
GROUNDING: Chỉ sử dụng thông tin từ nội dung tài liệu được cung cấp trong prompt. Tổng hợp và suy luận từ nội dung được cung cấp là hợp lệ — đây vẫn là grounded. Không bổ sung từ kiến thức bên ngoài. Chỉ khi câu hỏi nhắm tới chủ đề hoàn toàn không xuất hiện trong tài liệu (kể cả dưới tên gọi hay diễn đạt khác) → dùng đúng cụm "Tài liệu không đề cập đến điều này."
```
Lý do: bỏ chữ "thực sự vắng mặt" tuyệt đối, thêm điều kiện "kể cả dưới tên gọi/diễn đạt khác" để khớp logic 3 trạng thái và không mâu thuẫn với user-turn prompt.

---

## 5. Giải thích từng thay đổi (so với bản cũ)

- **"dựa CHỈ VÀO" → "dựa trên"** (balanced/permissive): chữ "CHỈ VÀO" khiến model diễn giải cứng nhắc theo khớp literal. Ràng buộc "không kiến thức ngoài" đã được nêu ở dòng riêng → không mất grounding.
- **Thêm nhánh (b) "liên quan một phần"**: đây là nhánh trực tiếp thu hồi nhóm false-positive lớn nhất. Model 2.5-flash follow tốt khi liệt kê rõ từng nhánh điều kiện.
- **Định nghĩa "LIÊN QUAN" tường minh**: chống mơ hồ — nêu rõ "kể cả từ ngữ/tên gọi/viết tắt khác" để model không từ chối khi câu hỏi dùng cụm khác tài liệu (đúng case Analytic Geometry).
- **Câu từ chối thành nhánh CUỐI + điều kiện chặt** ("hoàn toàn không chứa... liên quan"): đảo gánh nặng — model phải chứng minh "không liên quan" mới được từ chối, thay vì mặc định từ chối khi không khớp.
- **Giữ nguyên** rule độ dài, câu hỏi tổng quan, **bold** chứng cứ, ngôn ngữ → không đụng các hành vi đang đúng.

---

## 6. Ví dụ minh hoạ

### Case 1 — False-positive cũ (BẮT BUỘC sửa được)
- **Ngữ cảnh**: các đoạn trình bày norms (‖x‖₁, ‖x‖₂), inner product, orthogonality, Gram-Schmidt — KHÔNG có cụm literal "Analytic Geometry".
- **Câu hỏi**: "Analytic Geometry là gì? Các vấn đề liên quan."
- **Bản cũ (2 trạng thái)** → dễ trả: "Tài liệu không đề cập đến điều này." ❌ (false-positive)
- **Bản mới (balanced)** → (b): "Tài liệu không định nghĩa trực tiếp cụm 'Analytic Geometry', nhưng trình bày các chủ đề thuộc lĩnh vực này: **chuẩn (norms)** gồm Manhattan/Euclidean, **tích vô hướng (inner product)**, **trực giao (orthogonality)** và **quá trình Gram-Schmidt**. Tài liệu chưa nêu định nghĩa hình thức của 'Analytic Geometry' như một khái niệm tổng quát." ✅

### Case 2 — Câu hỏi đa phần (một phần có / một phần không)
- **Câu hỏi**: "Trình bày SVD và ứng dụng của nó trong xử lý ảnh y tế."
- **Ngữ cảnh**: có SVD (định nghĩa, phân rã), KHÔNG có ứng dụng ảnh y tế.
- **Bản mới (b)**: trả lời đầy đủ SVD từ tài liệu + "Tài liệu không đề cập ứng dụng trong xử lý ảnh y tế." ✅ (không từ chối toàn bộ)

### Case 3 — Thực sự ngoài tài liệu (c) — KHÔNG được nới
- **Câu hỏi**: "Thủ đô nước Pháp là gì?"
- **Ngữ cảnh**: tài liệu toán học, không liên quan.
- **Cả 3 bản** → "Tài liệu không đề cập đến điều này." ✅ (giữ chống hallucination — không được trả "Paris" từ kiến thức ngoài)

### Case 4 — Chống hallucination (ràng buộc bất biến)
- **Câu hỏi**: "Định lý X được chứng minh thế nào?" khi tài liệu chỉ phát biểu định lý, không có chứng minh.
- **Bản mới (b)**: nêu phát biểu có trong tài liệu + "Tài liệu không trình bày chứng minh." ✅ — KHÔNG được bịa bước chứng minh.

---

## 7. Khuyến nghị & Test

**Mặc định đề xuất: BALANCED (4B).** Lý do: thu hồi nhóm false-positive (b) — phần lớn lỗi — mà vẫn giữ câu từ chối cho nhóm (c) và cấm kiến thức ngoài. STRICT vẫn để sót một phần nhóm (b); PERMISSIVE có rủi ro "suy luận xa" cao hơn (dù vẫn trong context) → chỉ dùng nếu balanced vẫn còn từ chối sai nhiều.

**Risk:** Trung bình. Nguy cơ chính của permissive là model nối context quá đà → kiểm soát bằng yêu cầu "nêu rõ đó là suy luận". Balanced rủi ro thấp hơn.

**Rollback:** prompt là string thuần trong `_qa_prompt` → rollback = revert text. Không ảnh hưởng schema/retrieval.

**Test strategy (cho Tester) — A/B trên cùng bộ câu hỏi & cùng retrieval (hybrid GĐ2):**
1. Bộ case: gồm Case 1–4 ở trên + các câu hỏi thật từng bị false-positive trên tài liệu mai391.
2. **Metric chính**: false-positive rate = #(câu liên quan bị trả "không đề cập") / #(câu liên quan). Mục tiêu: giảm mạnh so với bản cũ.
3. **Metric ràng buộc (không được xấu đi)**: 
   - Hallucination rate: với câu nhóm (c), model có bịa từ kiến thức ngoài không? Phải = 0.
   - Faithfulness: câu trả lời nhóm (a)/(b) có bám context không (mọi khẳng định truy được về một đoạn ngữ cảnh).
4. So strict vs balanced vs permissive trên cùng bộ → chọn bản tối ưu false-positive với hallucination=0.
5. Cách chấm: có thể dùng chính Gemini làm judge (LLM-as-judge) chấm faithfulness + relevance, hoặc rà thủ công bộ nhỏ (~20-30 câu).

---

## 8. Action Items
- **[Backend]** Áp bản **BALANCED (4B)** vào `_qa_prompt` + cập nhật dòng GROUNDING (`_SYSTEM_TEXT`) như mục 4. Giữ nguyên phần context/question/lang ở cuối. (Để strict & permissive ở dạng comment/biến để A/B nếu muốn.)
- **[Tester]** Chạy A/B theo mục 7; báo cáo false-positive rate + hallucination rate trước/sau.
- **[PM]** Chốt bản mặc định dựa trên số đo của Tester.
