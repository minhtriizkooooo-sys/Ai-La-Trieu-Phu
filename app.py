import streamlit as st
from groq import Groq
import json
import pandas as pd
import os

# --- CẤU HÌNH HỆ THỐNG ---
# Lấy API Key từ môi trường của Render (Environment Variables)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def init_game():
    """Khởi tạo hoặc đặt lại trạng thái trò chơi"""
    st.session_state.step = 1
    st.session_state.current_q = None
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.used_helpers = {"call": False, "audience": False}
    st.session_state.money_levels = [
        "0", "200.000", "400.000", "600.000", "1.000.000", "2.000.000", 
        "3.000.000", "6.000.000", "10.000.000", "22.000.000", "30.000.000", 
        "40.000.000", "60.000.000", "85.000.000", "150.000.000"
    ]

def fetch_ai_question(level):
    """Gọi Groq API để lấy câu hỏi theo cấp độ"""
    if not GROQ_API_KEY:
        st.error("Chưa cấu hình GROQ_API_KEY trong Environment Variables!")
        return None

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""Tạo câu hỏi trắc nghiệm tiếng Việt 'Ai là triệu phú'. 
    Cấp độ khó: {level}/15 (câu 1 dễ, câu 15 cực khó).
    JSON format: {{"question": "Nội dung câu hỏi", "options": ["A", "B", "C", "D"], "answer_idx": 0}}"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        st.error(f"Lỗi kết nối AI: {e}")
        return None

def main():
    st.set_page_config(page_title="AI Millionaire Pro", layout="wide")
    
    # Kiểm tra khởi tạo session state
    if 'step' not in st.session_state:
        init_game()

    # --- GIAO DIỆN SIDEBAR ---
    st.sidebar.header("💰 MỨC THƯỞNG")
    for i in range(14, -1, -1):
        # Đánh dấu các mốc quan trọng (câu 5, 10, 15)
        is_milestone = (i + 1) % 5 == 0
        label = f"Câu {i+1}: {st.session_state.money_levels[i+1]} VNĐ"
        
        if st.session_state.step == i + 1:
            st.sidebar.markdown(f"**👉 :orange[{label}]**")
        else:
            if is_milestone:
                st.sidebar.markdown(f"**:red[{label}]**")
            else:
                st.sidebar.markdown(f" {label}")

    # --- GIAO DIỆN CHÍNH ---
    st.title("🏆 AI LÀ TRIỆU PHÚ - GROQ ENGINE")

    # Xử lý khi thắng cuộc
    if st.session_state.won:
        st.balloons()
        st.success(f"CHÚC MỪNG! Bạn đã trở thành TRIỆU PHÚ với {st.session_state.money_levels[-1]} VNĐ!")
        if st.button("Chơi lại"):
            init_game()
            st.rerun()
        return

    # Xử lý khi thua cuộc
    if st.session_state.game_over:
        st.error(f"Rất tiếc! Bạn đã dừng bước tại câu số {st.session_state.step}.")
        st.info(f"Số tiền thưởng của bạn: {st.session_state.money_levels[st.session_state.step-1]} VNĐ")
        if st.button("Thử lại từ đầu"):
            init_game()
            st.rerun()
        return

    # Load câu hỏi mới nếu cần
    if st.session_state.current_q is None:
        with st.spinner(f"AI đang soạn câu hỏi số {st.session_state.step}..."):
            st.session_state.current_q = fetch_ai_question(st.session_state.step)
            if st.session_state.current_q:
                st.rerun()

    q = st.session_state.current_q

    if q:
        # Hiển thị câu hỏi
        st.markdown(f"### Câu hỏi {st.session_state.step}:")
        st.info(q['question'])

        # Đáp án
        cols = st.columns(2)
        options_labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(q['options']):
            with cols[i % 2]:
                if st.button(f"{options_labels[i]}. {opt}", key=f"btn_{i}", use_container_width=True):
                    if i == q['answer_idx']:
                        st.toast("Chính xác!", icon="✅")
                        if st.session_state.step == 15:
                            st.session_state.won = True
                        else:
                            st.session_state.step += 1
                            st.session_state.current_q = None
                        st.rerun()
                    else:
                        st.session_state.game_over = True
                        st.rerun()

        # Trợ giúp
        st.divider()
        st.subheader("🆘 Quyền trợ giúp")
        h_col1, h_col2 = st.columns(2)
        
        with h_col1:
            if st.button("📞 Gọi điện cho người thân", disabled=st.session_state.used_helpers['call'], use_container_width=True):
                st.session_state.used_helpers['call'] = True
                st.session_state.show_call = True
            
            if st.session_state.get('show_call'):
                st.write(f"🤖 **Người thân trả lời:** 'Theo mình biết thì đáp án đúng là **{options_labels[q['answer_idx']]}**.'")
                
        with h_col2:
            if st.button("📊 Hỏi ý kiến khán giả", disabled=st.session_state.used_helpers['audience'], use_container_width=True):
                st.session_state.used_helpers['audience'] = True
                st.session_state.show_audience = True
            
            if st.session_state.get('show_audience'):
                # Giả lập biểu đồ khán giả (tỉ lệ đúng giảm dần theo độ khó)
                data = [5, 5, 5, 5]
                correct_boost = max(10, 70 - (st.session_state.step * 4)) 
                data[q['answer_idx']] += correct_boost
                chart_data = pd.DataFrame(data, index=["A", "B", "C", "D"], columns=["%"])
                st.bar_chart(chart_data)

# --- CHẠY APP ---
if __name__ == "__main__":
    main()