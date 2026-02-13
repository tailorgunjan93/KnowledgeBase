"""Skills management module."""
import streamlit as st
from database.db_manager import DatabaseManager
from modules.session import SessionManager
from utils.helpers import format_timestamp


# Predefined skill templates
SKILL_TEMPLATES = {
    "Technical Writer": {
        "description": "Clear, precise technical writing style",
        "template": "Write in a clear, technical style. Use precise terminology and provide detailed explanations. Format with headers and bullet points where appropriate."
    },
    "Creative Writer": {
        "description": "Engaging, creative writing style",
        "template": "Write in an engaging, creative style. Use vivid language, metaphors, and storytelling techniques to make the content interesting and memorable."
    },
    "Formal Business": {
        "description": "Professional business communication",
        "template": "Write in a formal business tone. Be professional, concise, and action-oriented. Use business terminology appropriately."
    },
    "ELI5 (Explain Like I'm 5)": {
        "description": "Simple explanations for complex topics",
        "template": "Explain this in very simple terms that a 5-year-old could understand. Use simple words, analogies, and examples from everyday life."
    },
    "Academic": {
        "description": "Scholarly, well-researched style",
        "template": "Write in an academic style. Be objective, well-structured, and support points with reasoning. Use formal language and proper terminology."
    },
    "Casual & Friendly": {
        "description": "Conversational, approachable tone",
        "template": "Write in a casual, friendly tone. Use simple language, contractions, and a conversational style. Be warm and approachable."
    },
    "Concise & Direct": {
        "description": "Brief, to-the-point responses",
        "template": "Be extremely concise and direct. Get straight to the point without unnecessary elaboration. Use short sentences and bullet points."
    },
    "Code Helper": {
        "description": "Focus on code examples and implementation",
        "template": "Provide clear code examples and implementation details. Include comments in code. Explain technical concepts with practical examples."
    }
}


def render_skills_page(db: DatabaseManager):
    """
    Render the skills management page.
    
    Args:
        db: Database manager instance
    """
    user_id = SessionManager.get_user_id()
    if not user_id:
        st.error("Please log in to manage skills")
        return
    
    st.title("🎯 Skills Manager")
    
    st.markdown("""
    Skills let you customize how the AI responds to your questions. Create skills to control the tone, 
    style, and format of AI responses.
    """)
    
    # Create new skill section
    with st.expander("➕ Create New Skill", expanded=False):
        st.markdown("### Create from Template")
        
        template_name = st.selectbox(
            "Choose a template",
            options=["Custom"] + list(SKILL_TEMPLATES.keys())
        )
        
        if template_name != "Custom":
            template = SKILL_TEMPLATES[template_name]
            default_name = template_name
            default_desc = template['description']
            default_template = template['template']
        else:
            default_name = ""
            default_desc = ""
            default_template = ""
        
        skill_name = st.text_input("Skill Name", value=default_name)
        skill_desc = st.text_input("Description", value=default_desc)
        skill_prompt = st.text_area(
            "Prompt Template",
            value=default_template,
            height=150,
            help="This instruction will be added to the AI's system message when this skill is applied"
        )
        
        if st.button("Create Skill", type="primary"):
            if skill_name and skill_prompt:
                skill_id = db.create_skill(
                    user_id=user_id,
                    name=skill_name,
                    description=skill_desc,
                    prompt_template=skill_prompt
                )
                st.success(f"✅ Created skill '{skill_name}'!")
                st.rerun()
            else:
                st.error("Please provide a name and prompt template")
    
    # List existing skills
    st.markdown("---")
    st.markdown("### Your Skills")
    
    skills = db.get_user_skills(user_id)
    
    if not skills:
        st.info("No skills yet. Create one above to get started!")
    else:
        for skill in skills:
            with st.expander(f"🎯 {skill['name']}", expanded=False):
                st.markdown(f"**Description:** {skill['description']}")
                st.markdown(f"**Created:** {format_timestamp(skill['created_at'])}")
                
                st.markdown("**Prompt Template:**")
                st.code(skill['prompt_template'], language=None)
                
                # Edit mode
                if st.checkbox("Edit", key=f"edit_{skill['id']}"):
                    new_name = st.text_input("Name", value=skill['name'], key=f"name_{skill['id']}")
                    new_desc = st.text_input("Description", value=skill['description'], key=f"desc_{skill['id']}")
                    new_prompt = st.text_area(
                        "Prompt Template",
                        value=skill['prompt_template'],
                        key=f"prompt_{skill['id']}",
                        height=150
                    )
                    
                    col1, col2 = st.columns(2)
                    if col1.button("Save Changes", key=f"save_{skill['id']}"):
                        db.update_skill(
                            skill_id=skill['id'],
                            user_id=user_id,
                            name=new_name,
                            description=new_desc,
                            prompt_template=new_prompt
                        )
                        st.success("Skill updated!")
                        st.rerun()
                
                # Delete button
                if st.button(f"🗑️ Delete Skill", key=f"del_{skill['id']}"):
                    if db.delete_skill(skill['id'], user_id):
                        st.success("Skill deleted!")
                        st.rerun()
