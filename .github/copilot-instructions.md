## Coding Guidelines: Project Nifty 500 Live Sentiment Analysis

**Project Goal:** Provide a user dashboard for tracking media sentiment related to Nifty 500 stocks.

**These guidelines are for LLM coding agents. Strict adherence is crucial for efficient collaboration and project success.**

**I. Core Principles (Non-Negotiable):**

*   **Understand the "Why":** Before writing *any* code, ensure you fully grasp the task's objective and its contribution to the overall project goal.  The goal is to solve a problem, not just write code.
*   **Ask Questions Immediately:** If *anything* is unclear, ask clarifying questions *immediately* in the Project Chat. Ambiguity leads to wasted effort and is unacceptable.
*   **Clarity and Readability are Paramount:** Code must be easily understood by humans and other agents.  Favor clean, well-structured, and thoroughly commented code over unnecessary complexity. This is critical for debugging and iteration.
*   **Prioritize Maintainability:** Write code that is easy to modify, debug, and extend in the future.  Avoid shortcuts or hacks that create technical debt.  This is especially important in the financial domain, where requirements often change.
*   **Follow Established Conventions:** Adhere to the coding style, architecture (see `ARCHITECTURE.md`), and patterns already established in the project. Consistency is crucial. Refer to the [Agent's Project Log](../agent_project_log.md) for project-specific decisions.
*   **Test Thoroughly and Continuously:** Every piece of code written *must* be tested to ensure it functions correctly and doesn't introduce regressions.  Write unit tests, integration tests, and consider edge cases. Testing is an ongoing part of the development process, *not* an afterthought.
*   **Communicate Proactively:**  If you encounter problems, have questions, or need clarification, communicate proactively and clearly in the Project Chat.  Provide context and specific details. It's better to ask early than to waste time.
*   **Iterative Development & Learning:** Focus on delivering correct results efficiently, iterating quickly based on feedback. Learn from each iteration and incorporate feedback to improve.

**II. Task Execution (Step-by-Step Procedure):**

1.  **Task Understanding and Confirmation (Critical First Steps):**
    *   **Mandatory Clarification:** If a task description is ambiguous in *any* way, ask specific questions to clarify the requirements, expected inputs, outputs, and any constraints.
    *   **Confirm Understanding:** Before starting, briefly summarize your understanding of the task back to the user to ensure alignment. Example: "So, you want me to [summarize task], and the expected output is [describe output]? Is that correct?"
    *   **Identify Dependencies:** Determine if the task depends on other parts of the codebase or other tasks.  Flag any dependencies or potential conflicts *immediately*.

2.  **Coding Phase (Clean, Efficient, and Well-Documented):**
    *   **Modular Approach:** Break down complex tasks into smaller, manageable modules or functions.  Avoid monolithic functions that are difficult to understand and test.
    *   **Iterative Development (Key for Speed and Accuracy):** Implement features in small, testable increments. Don't try to build everything at once.  Focus on getting a basic version working quickly, then iterate and improve based on feedback and testing.
    *   **Comprehensive Comments and Documentation:**
        *   Objective for each file must be clearly defined in [Project Architecture](../architecture.md). For each file you create, first create its entry in [Project Architecture](../architecture.md) and take the user's confirmation if the objective is correct and based on that objective, make the code changes. For updating consult the [Project Architecture](../architecture.md) and then update keeping objectives in check.
        *   Write clear and concise comments explaining the *purpose* of code blocks, functions, and complex logic.
        *   Write the purpose of each file/module at the top
        *   For *important decisions or complex logic*, add comments *directly in the code* to explain the reasoning (for future reference, including your own).
        *   Document public APIs and significant internal logic.
        *   follow google style docstrings for documentation.
        *   After each code update, make sure to update the module/file documentation.
    *   **Robust Error Handling:** Implement comprehensive error handling to gracefully handle unexpected inputs or situations.  Use `try-except` blocks in Python to catch and handle potential exceptions.
    *   **Vectorized Operations (Performance and Readability):**
        *   Utilize libraries like NumPy and Pandas for vectorized operations on data to improve performance.
        *   Prioritize readability even when using vectorized operations:
            *   Use meaningful variable names.
            *   Add comments to explain the logic of vectorized operations, especially if they are complex.
            *   Break down complex operations into smaller, well-defined steps for clarity.
    *   **Mandatory Reuse of Existing Modules/Services:**
        *   *Before* implementing *any* new functionality, thoroughly check for existing helper modules or services within the codebase. Refer to [Project Architecture](../architecture.md) for reference.
        *   *Do not* re-implement existing functionality. This is *especially critical for database operations*. Use the provided database interaction modules.
        *   If you identify redundancy, create a *new* helper module, document it, and refactor existing code to use it.
    *   **Secure API Key Handling:**
        *   **Never** hardcode API keys directly within the code. This is a major security risk.
        *   Store API keys in environment variables. Access them in Python using `os.environ.get('API_KEY_NAME')`.
        *   If using a `.env` file for local development, *ensure it is added to `.gitignore`* to prevent accidental commits to the repository.

3.  **Code Review and Testing (Essential for Quality):**
    *   **Self-Review:** Before submitting code, *always* review it yourself for clarity, correctness, adherence to these guidelines, and potential improvements.
    *   **Comprehensive Testing:**
        *   **Unit Tests:** Write unit tests to verify the functionality of individual components or functions.
        *   **Integration Tests:** Write integration tests to ensure different parts of the system work together correctly.
        *   **Edge Cases and Boundary Conditions:** Test for edge cases, invalid inputs, and boundary conditions to ensure robustness. This is *especially important* in financial applications.
        *   **Provide Test Results:** Clearly communicate the test results and any identified issues in the Project Chat.

**III. Collaboration and Communication Protocols (Project Chat):**

*   **Preferred Communication Channel:** Project Chat (for general communication and questions). *Important decisions or reasoning should also be documented as comments within the code itself.*
*   **Frequency of Updates:** Provide updates *after the completion of each sub-task*.
*   **Reporting Issues and Blockers:** *Immediately* report any issues, blockers, or unexpected problems encountered.  Provide detailed information and context in the Project Chat.
*   **Asking Questions (Critical for Efficiency):**
    *   When you are unsure about *any* aspect of the task, ask questions in the Project Chat. This is crucial for efficient task execution.
    *   Be specific and provide context when asking questions.
    *   Include relevant code snippets or error messages.
    *   Clearly state what you have already tried or investigated (if applicable).
*   **Responding to Feedback:** Actively consider and respond to feedback provided by the user in the Project Chat.  Ask clarifying questions if feedback is unclear.

**IV. Technical Specifications:**

*   **Programming Languages:** Python
*   **Frameworks:** Streamlit
*   **Version Control System:** Git (Branching strategy: Follow project-specific strategy if one exists; otherwise, use feature branches. Consult `ARCHITECTURE.md`.)
*   **Package Management:** `uv pip install` instead of `pip install` (Use virtual environments for each project).
*   **Development Environment:**
    *   **IDE:** VSCode is the primary IDE.
*   **CI/CD:** Utilize GitHub Actions to schedule periodic service runs.

**V. Streamlit-Specific Guidelines:**

*   **Clear and Effective Data Visualization:** Focus on presenting data in a clear, concise, and visually appealing manner.
*   **User-Friendly Interface:** Ensure dashboards are intuitive to navigate and easy to use.
*   **Performance Optimization (Essential for Responsiveness):**
    *   **Caching:** Use Streamlit's caching mechanisms (`@st.cache_data` and `@st.cache_resource`) to avoid redundant computations.  Understand the difference: `@st.cache_data` is for data dependent on function *inputs*; `@st.cache_resource` is for shared resources like database connections.
    *   **Efficient Data Loading:** Employ efficient methods for loading and processing large datasets (e.g., vectorized operations, chunking if necessary).
    *   **Widget Optimization:**  Avoid unnecessary re-renders by using appropriate widgets and minimizing widget updates.

**VI. Financial Domain Considerations (Critical):**

*   **Data Accuracy and Integrity:** Data accuracy and security are of paramount importance. Validate all data and analysis results rigorously.
*   **Documentation of Assumptions and Methodologies:** Clearly document all assumptions and methodologies used in any analysis related to the financial domain.
* **Strategy Execution Analysis:**
    *   Prioritize data accuracy and integrity.
    *   Clearly document all assumptions and methodologies used in the analysis.
    *   Validate analysis results thoroughly and cross-reference with reliable sources.
    *   Pay attention to financial domain best practices and regulations.
    *   Present analysis results in a clear and understandable format.
    *   Document data sources and data cleaning steps.

**VII. Agent's Project Log (`agent_project_log.md` - Root Directory):**

*   **Purpose:** This log is for your internal use to track project-specific information, decisions, issues, and resolutions.  It serves as a memory aid and helps in consistent decision-making and problem-solving over time.  *Maintaining this log is mandatory.*
*   **Mandatory Logging:** *Every* change, decision, bug fix, or significant learning *must* be documented in the Agent's Project Log, timestamped with the current date.
*   **Format:** Use a simple and easily searchable format (Markdown - `.md`) within the project directory. This log is for your own benefit and should be maintained in a way that is most helpful to you.
*   **Content to Log:**
    *   **Decision Log:** Record *significant* decisions made during development, especially when there were multiple options considered. Document the reasoning behind the chosen approach.
    *   **Bug/Issue Log:** When encountering bugs or issues (even if you resolve them yourself), briefly log them, including:
        *   A short description of the bug/issue.
        *   Steps taken to diagnose the issue.
        *   The solution implemented.
        *   Link to relevant code changes (commit or file).
    *   **Learning Log:** Record any new things learned about the project, libraries, or the financial domain that might be useful in the future.
    *   **Gotchas and Reminders:** Note down any project-specific "gotchas" or recurring issues to avoid in the future.
*   **Storage Location:** Store the Agent's Project Log as a file named `agent_project_log.md` in the root directory of the project repository. This ensures it is easily accessible within the project context and can be version controlled along with the code.
*   **Organization:** Organize entries within `agent_project_log.md` by date and category (Decision, Bug, Learning, Reminder) for better readability and searchability. Use Markdown formatting (headings, lists, code blocks) to improve organization.  Get the present date using the `date` command in bash.

**Project Architecture:** Refer to the `ARCHITECTURE.md` document for details on the overall system design, data flow, and component interactions.
