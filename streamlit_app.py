import time

import httpx
import streamlit as st
from decouple import config
from fastapi import Response, status
from loguru import logger

LANGUAGES = ["Python", "TypeScript", "JavaScript"]


def on_delete_success():
    """Callback after successful deletion"""
    # st.session_state.current_view = "list"
    st.session_state.redirect_to_list = True


def create_streamlit_expander(snippet: dict) -> None:
    """Create Streamlit expander to view snippets"""

    with st.expander(f"{snippet["title"]}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            if snippet.get("description"):
                st.write(f"Description: {snippet['description']}")
        with col2:
            st.write(f"Created: {snippet['created_at'].split('T')[0]}")

        st.code(snippet["code"], language=snippet["language"].lower())

        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            if snippet.get("tags"):
                st.write(f"Tags: {snippet['tags']}")
        with col2:
            st.write(f"Favourite: {snippet["favorite"]}")
        with col3:
            st.write(f"Updated: {snippet['updated_at'].split('T')[0]}")


def display_list_snippets(snippets: list[dict]) -> None:
    """Display the snippets"""

    st.title("List of snippets")
    for snippet in snippets:
        create_streamlit_expander(snippet)


def display_create_snippet_form():
    """Add form to collect snippet data"""

    with st.form("Snippet"):
        title = st.text_input("Title")
        code = st.text_area("Code")
        language = st.selectbox("Language", LANGUAGES)
        description = st.text_input("Description")
        tags = st.text_input("Tags (Comma separated)")
        submitted = st.form_submit_button("Add")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("⚠️ Title is required.")
        if not code.strip():
            errors.append("⚠️ Code is required.")
        if errors:
            for err in errors:
                st.warning(err)
            submitted = False
        else:
            st.success("✅ Snippet form submitted successfully!")

    snippet = {
        "title": title,
        "code": code,
        "description": description,
        "favourite": False,
        "language": language,
        "tags": tags,
    }

    return submitted, snippet


def display_snippets(snippet_ids: list[int], op: str) -> int:
    """Add dropdown to list snippets for get/delete operations"""

    with st.form("Snippet IDs"):
        snippet_id = st.selectbox("Snippet ID", snippet_ids)
        action = "Find" if op == "get" else "Delete"
        submitted = st.form_submit_button(action)

    if submitted:
        if not snippet_id:
            st.warning("⚠️ Snippet ID is required.")

    return submitted, {
        "snippet_id": snippet_id,
    }


def display_search_snippet():
    """Capture search parameters and display the results"""

    with st.form("Search term"):
        term = st.text_input("Term to search for")
        language = st.selectbox("Language", [None] + LANGUAGES)
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not term.strip():
            st.warning("⚠️ Title is required.")

    return submitted, {
        "term": term,
        "language": language,
    }


st.set_page_config(
    page_title="Snipster App",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = config("API_URL", "http://127.0.0.1:8000")

if "view_id" not in st.session_state:
    st.session_state.view_id = None
if "current_view" not in st.session_state:
    st.session_state.current_view = "list"
if "redirect_to_list" not in st.session_state:
    st.session_state.redirect_to_list = False
if "menu_key" not in st.session_state:
    st.session_state.menu_key = 0

view_to_index = {
    "list": 0,
    "add": 1,
    "get": 2,
    "search": 3,
    "delete": 4,
    "favourite": 5,
    "tag": 6,
}

if st.session_state.redirect_to_list:
    st.session_state.current_view = "list"
    st.session_state.redirect_to_list = False
    st.session_state.menu_key += 1

with st.sidebar:
    st.title("Snipster")
    menu = st.radio(
        "Navigation",
        [
            "List Snippets",
            "Add Snippets",
            "Get Snippet",
            "Search Snippets",
            "Delete Snippet",
            "Toggle Favourite",
            "Tag Snippets",
        ],
        key=f"menu_{st.session_state.menu_key}",
        index=view_to_index.get(st.session_state.current_view, "list"),
    )


def set_session_states():
    """Set session state values to their respective endpoints"""
    if not st.session_state.redirect_to_list:
        if menu == "List Snippets":
            st.session_state.current_view = "list"
        elif menu == "Add Snippets":
            st.session_state.current_view = "add"
        elif menu == "Get Snippet":
            st.session_state.current_view = "get"
        elif menu == "Search Snippets":
            st.session_state.current_view = "search"
        elif menu == "Delete Snippet":
            st.session_state.current_view = "delete"
        elif menu == "Toggle Favourite":
            st.session_state.current_view = "favourite"
        else:
            st.session_state.current_view = "tag"


def list_snippets(url: str) -> Response:
    """List snippets from the endpoint"""
    response = httpx.get(url)
    return response


def create_snippet(url: str, snippet: dict[str, str]) -> Response:
    """Create Snippet"""
    response = httpx.post(url, json=snippet)
    return response


def get_snippet(url: str, snippet_id: int) -> Response:
    """Get Snippet"""

    url = url.format(snippet_id=snippet_id)
    response = httpx.get(url)
    return response


def search_snippet(url: str, term: str, language: str | None = None) -> Response:
    """Search snippet"""

    if language:
        url = f"{url}&language={language}"
        url = url.format(term=term, language=language)
    else:
        url = url.format(term=term)
    logger.info(url)
    response = httpx.get(url)
    return response


def delete_snippet(url: str, snippet_id: int) -> Response:
    """Delete Snippet"""

    url = url.format(snippet_id=snippet_id)
    response = httpx.delete(url)
    return response


set_session_states()

urls = {
    "list_snippet": "/snippets/v1/list/",
    "add_snippet": "/snippets/v1/",
    "get_snippet": "/snippets/v1/{snippet_id}",
    "search_snippet": "/snippets/v1/search/?term={term}",
    "delete_snippet": "/snippets/v1/{snippet_id}",
}

if st.session_state.current_view == "list":
    list_endpoint = urls.get("list_snippet")
    list_endpoint_url = f"{API_URL}{list_endpoint}"
    snippets = list_snippets(list_endpoint_url)
    if "detail" in snippets.json():
        st.error(f"❌ {snippets.json()['detail']}")
    else:
        display_list_snippets(snippets.json())
elif st.session_state.current_view == "add":
    add_endpoint = urls.get("add_snippet")
    add_endpoint_url = f"{API_URL}{add_endpoint}"
    submitted, snippet = display_create_snippet_form()

    if submitted:
        logger.info("Snippet Form submitted")
        response = create_snippet(add_endpoint_url, snippet)
        if response.status_code == status.HTTP_200_OK:
            logger.info("Snippet successfully created")
            st.success("✅ Snippet successfully created!")
        elif response.status_code == status.HTTP_409_CONFLICT:
            logger.error(" Duplicate snippet found")
            st.error(" Duplicate snippet found")
        else:
            logger.error(" Repository error")
            st.error("❌ Repository error")
elif st.session_state.current_view == "get":
    get_endpoint = urls.get("get_snippet")
    get_endpoint_url = f"{API_URL}{get_endpoint}"

    list_endpoint_url = f"{API_URL}{urls.get("list_snippet")}"
    snippets = list_snippets(list_endpoint_url)
    if "detail" in snippets.json():
        st.error(f"❌ {snippets.json()['detail']}")
    else:
        snippet_ids = [snippet.get("id") for snippet in snippets.json()]
        submitted, snippet = display_snippets(snippet_ids, "get")

        if submitted:
            response = get_snippet(get_endpoint_url, snippet.get("snippet_id"))
            st.subheader(f"Snippet details for snippet '{snippet.get("snippet_id")}'")
            create_streamlit_expander(response.json())

            if response.status_code == status.HTTP_200_OK:
                logger.info(
                    f"Succesfully fetched snippet '{snippet.get("snippet_id")}'"
                )
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                logger.error(
                    f"No snippet found for snippet '{snippet.get("snippet_id")}'"
                )
                st.error(
                    f"❌ No snippet found for snippet '{snippet.get("snippet_id")}'"
                )
            else:
                logger.error(" Repository error")
                st.error("❌ Repository error")
elif st.session_state.current_view == "search":
    search_endpoint = urls.get("search_snippet")
    search_endpoint_url = f"{API_URL}{search_endpoint}"

    submitted, params = display_search_snippet()
    if submitted:
        response = search_snippet(search_endpoint_url, **params)
        st.subheader("Search results:")
        if response.status_code == status.HTTP_200_OK:
            logger.info(f"Search returned {len(response.json())} snippets")
            st.success(f"✅ Search returned {len(response.json())} snippets")
            for snippet in response.json():
                create_streamlit_expander(snippet)
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            logger.error("Search returned no snippets")
            st.error("❌ Search returned no snippets")
        else:
            logger.error(" Repository error")
            st.error("❌ Repository error")
elif st.session_state.current_view == "delete":
    delete_endpoint = urls.get("delete_snippet")
    delete_endpoint_url = f"{API_URL}{delete_endpoint}"

    list_endpoint_url = f"{API_URL}{urls.get("list_snippet")}"
    snippets = list_snippets(list_endpoint_url)
    if "detail" in snippets.json():
        st.error(f"❌ {snippets.json()['detail']}")
    else:
        snippet_ids = [snippet.get("id") for snippet in snippets.json()]
        submitted, snippet = display_snippets(snippet_ids, "delete")

        if submitted:
            response = delete_snippet(delete_endpoint_url, snippet.get("snippet_id"))
            st.subheader(f"Snippet details for '{snippet.get("snippet_id")}'")
            # create_streamlit_expander(response.json())

            if response.status_code == status.HTTP_200_OK:
                logger.info(
                    f"Succesfully deleted snippet '{snippet.get("snippet_id")}'"
                )
                st.success(
                    f"✅ Succesfully deleted snippet '{snippet.get("snippet_id")}'"
                )

                time.sleep(1)
                on_delete_success()
                st.rerun()
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                logger.error(
                    f"No snippet found for snippet '{snippet.get("snippet_id")}'"
                )
                st.error(
                    f"❌ No snippet found for snippet '{snippet.get("snippet_id")}'"
                )
            else:
                logger.error(" Repository error")
                st.error("❌ Repository error")
