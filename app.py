import streamlit as st
from groq import Groq
import json
import pandas as pd
import os

# --- CẤU HÌNH HỆ THỐNG ---
# Tên biến trong Python KHÔNG ĐƯỢC chứa dấu gạch ngang. Đã đổi thành dấu gạch dưới.
# Đảm bảo trên Render bạn đã đặt tên Key là: Ai_La_Trieu_Phu_API
API_KEY_FROM_ENV = os.environ.get("Ai_La_Trieu_Phu_API")

def init_game():
    """Khởi tạo hoặc đặt lại trạng thái trò chơi"""
    st.session_state.step = 1
    st.session_state.current_q = None
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.used_helpers = {"call": False, "audience": False}
    # Danh sách 16 phần tử để tránh lỗi Index (từ mốc 0 đến câu 15)
    st.session_state.money_levels = [
        "0", "200.000", "400.000", "600.000", "1.000.000", "2.000.000", 
        "3.000.000", "6.000.000", "10.000.000", "22.000.000", "30.000.000", 
        "40.000.000", "60.000.000", "85.000.000", "150.000.000", "250.000.000"
    ]

def fetch_ai_question(level):
    """Gọi Groq API để lấy câu hỏi theo cấp độ"""
    if not API_KEY_FROM_ENV:
        st.error("Chưa cấu hình API Key trong Environment Variables trên Render (Ai_La_Trieu_Phu_API)!")
        return None

    client = Groq(api_key=API_KEY_FROM_ENV)
    
    prompt = f"""Tạo một câu hỏi trắc nghiệm tiếng Việt cho trò chơi 'Ai là triệu phú'. 
    Cấp độ khó: {level}/15. 
    Yêu cầu trả về định dạng JSON nguyên bản, không giải thích thêm: 
    {{"question": "Nội dung câu hỏi", "options": ["A", "B", "C", "D"], "answer_idx": 0}}"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return None

def main():
    st.set_page_config(page_title="AI Millionaire Pro", layout="wide")
    
    # Kiểm tra khởi tạo session state
    if 'step' not in st.session_state:
        init_game()

    # --- GIAO DIỆN SIDEBAR (BẢNG MỨC THƯỞNG) ---
    st.sidebar.header("💰 MỨC THƯỞNG")
    for i in range(15, 0, -1):
        is_milestone = i % 5 == 0
        label = f"Câu {i}: {st.session_state.money_levels[i]} VNĐ"
        
        if st.session_state.step == i:
            st.sidebar.markdown(f"**👉 :orange[{label}]**")
        else:
            if is_milestone:
                st.sidebar.markdown(f"**:red[{label}]**")
            else:
                st.sidebar.markdown(f"{label}")

    # --- GIAO DIỆN CHÍNH ---
    st.title("🏆 AI LÀ TRIỆU PHÚ")

    if st.session_state.won:
        st.balloons()
        st.success(f"CHÚC MỪNG! Bạn đã vượt qua câu 15 và nhận {st.session_state.money_levels[15]} VNĐ!")
        if st.button("Chơi lại"):
            init_game()
            st.rerun()
        return

    if st.session_state.game_over:
        st.error(f"Rất tiếc! Bạn đã dừng bước.")
        safe_step = (st.session_state.step // 5) * 5
        st.info(f"Tiền thưởng nhận được: {st.session_state.money_levels[safe_step]} VNĐ")
        if st.button("Chơi lại từ đầu"):
            init_game()
            st.rerun()
        return

    if st.session_state.current_q is None:
        with st.spinner(f"AI đang chuẩn bị câu hỏi số {st.session_state.step}..."):
            new_q = fetch_ai_question(st.session_state.step)
            if new_q:
                st.session_state.current_q = new_q
                st.rerun()

    q = st.session_state.current_q
    if q:
        st.markdown(f"### Câu hỏi {st.session_state.step}:")
        st.info(q['question'])

        cols = st.columns(2)
        options_labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(q['options']):
            with cols[i % 2]:
                if st.button(f"{options_labels[i]}. {opt}", key=f"btn_{i}", use_container_width=True):
                    if i == q['answer_idx']:
                        st.success("ĐÁP ÁN CHÍNH XÁC!")
                        if st.session_state.step == 15:
                            st.session_state.won = True
                        else:
                            st.session_state.step += 1
                            st.session_state.current_q = None
                            st.session_state.show_call = False
                            st.session_state.show_audience = False
                        st.rerun()
                    else:
                        st.session_state.game_over = True
                        st.rerun()

        st.divider()
        st.subheader("🆘 Quyền trợ giúp")
        h_col1, h_col2 = st.columns(2)
        
        with h_col1:
            if st.button("📞 Gọi cho người thân", disabled=st.session_state.used_helpers['call'], use_container_width=True):
                st.session_state.used_helpers['call'] = True
                st.session_state.show_call = True
            
            if st.session_state.get('show_call'):
                st.warning(f"🤖 Người thân: 'Mình nghĩ đáp án đúng là **{options_labels[q['answer_idx']]}**.'")
                
        with h_col2:
            if st.button("📊 Ý kiến khán giả", disabled=st.session_state.used_helpers['audience'], use_container_width=True):
                st.session_state.used_helpers['audience'] = True
                st.session_state.show_audience = True
            
            if st.session_state.get('show_audience'):
                data = [10, 10, 10, 10]
                correct_rate = max(15, 80 - (st.session_state.step * 4)) 
                data[q['answer_idx']] = correct_rate
                rem = (100 - correct_rate) // 3
                for idx in range(4):
                    if idx != q['answer_idx']: data[idx] = rem
                
                chart_data = pd.DataFrame(data, index=["A", "B", "C", "D"], columns=["% Tỷ lệ"])
                st.bar_chart(chart_data)

if __name__ == "__main__":
    main()
