"""Skills Page for managing custom AI personas."""
import streamlit as st
from domain.models import Skill
from data.repositories.settings_repository import SkillRepository
from ui.components import load_css

SKILL_TEMPLATES = {
    "Technical Writer": {
        "description": "Clear, precise technical writing",
        "template": "Write in a clear, technical style. Use precise terminology and provide detailed explanations."
    },
    "Creative Writer": {
        "description": "Engaging, creative storytelling",
        "template": "Write in an engaging, creative style. Use vivid language and metaphors."
    },
    "ELI5": {
        "description": "Simple explanations",
        "template": "Explain this in very simple terms that a 5-year-old could understand."
    },
    "Professional": {
        "description": "Formal business tone",
        "template": "Write in a formal business tone. Be professional, concise, and action-oriented."
    }
}

def render_skills_page():
    load_css()
    skill_repo = SkillRepository()
    user_id = st.session_state.get('user_id')
    
    if not user_id:
        st.warning("Please log in.")
        return

    st.markdown("## 🎯 Skills Manager")
    st.markdown("Create custom personas to control the AI's interaction style.")

    # Top: Create Skill
    with st.expander("➕ Create New Skill", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            template_choice = st.selectbox("Load Template", ["Custom"] + list(SKILL_TEMPLATES.keys()))
        
        # Defaults
        d_name, d_desc, d_templ = "", "", ""
        if template_choice != "Custom":
            t = SKILL_TEMPLATES[template_choice]
            d_name = template_choice
            d_desc = t['description']
            d_templ = t['template']

        with st.form("create_skill"):
            name = st.text_input("Name", value=d_name)
            desc = st.text_input("Description", value=d_desc)
            prompt = st.text_area("System Prompt", value=d_templ, height=100)
            
            if st.form_submit_button("Create Skill", type="primary"):
                if name and prompt:
                    new_skill = Skill(
                        user_id=user_id,
                        name=name,
                        description=desc,
                        prompt_template=prompt
                    )
                    skill_repo.create(new_skill)
                    st.success("Skill created!")
                    st.rerun()
                else:
                    st.error("Name and Prompt are required.")

    # List Skills
    skills = skill_repo.get_user_skills(user_id)
    if not skills:
        st.info("No skills found. Create your first one above!")
    else:
        st.markdown("### Your Skills")
        for skill in skills:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{skill.name}**")
                    st.caption(skill.description)
                with c2:
                    if st.button("🗑️", key=f"del_{skill.id}"):
                        skill_repo.delete(skill.id)
                        st.rerun()
                
                with st.expander("Edit Prompt"):
                    new_prompt = st.text_area("Prompt", skill.prompt_template, key=f"p_{skill.id}")
                    if st.button("Update", key=f"upd_{skill.id}"):
                        # Update logic (repo needs update endpoint or similar)
                        # For now, simplest is delete/recreate or direct SQL update if repo supports it
                        # Assuming repo has update or we add it. 
                        # Let's check repo capability. If missing, we might need to add it.
                        # For parity, v1 had update.
                        skill.prompt_template = new_prompt
                        # skill_repo.update(skill) # TODO: Implement update in repo
                        st.warning("Update function pending in Repository.")
