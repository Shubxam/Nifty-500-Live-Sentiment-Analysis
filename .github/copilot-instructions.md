## Guideline for Coding Agents: Project Nifty 500 Live Sentiment Analysis

**Aim of the project:** This project provides users with a dashboard where they can come and track the media sentiments related to the stocks of their interest. 

**Purpose of the Document:** This document outlines the guidelines for coding agents assisting with the Nifty 500 Live Sentiment Analysis project. Following these guidelines will ensure effective collaboration, code quality, and faster progress towards project goals, specifically within the financial domain.

**I. Core Principles & Mindset:**

* **Understand the Goal Clearly:**  Before starting any task, ensure you fully understand the objective.  **Don't hesitate to ask clarifying questions immediately if anything is unclear.** The goal is to solve a specific problem or implement a feature that contributes to the overall project goals, not just to write code. **Ambiguity leads to wasted iteration.**
* **Prioritize Clarity and Readability:**  Code should be easy to understand, both for humans and other agents.  Focus on writing clean, well-structured, and commented code.  Favor clarity over unnecessary complexity.  This is crucial for efficient iteration and debugging.
* **Maintainability is Key:**  Think long-term. Write code that is easy to modify, debug, and extend in the future. Avoid hacks or shortcuts that might create technical debt.  This is especially important in the financial domain where requirements can evolve.
* **Follow Established Conventions:** Adhere to the coding style, architecture, and patterns already established in the project. Consistency is crucial for maintainability and collaboration. **Refer to project-specific documentation (Section IV) if available and the Agent's Project Log (Section VIII).**
* **Test Thoroughly and Iteratively:**  Every piece of code written must be tested to ensure it functions as expected and doesn't introduce regressions. Write unit tests, integration tests, and consider edge cases. **Testing should be an ongoing part of the development process, not an afterthought, to enable faster iteration.**
* **Communicate Proactively and Ask Questions:**  If you encounter problems, have questions, or need clarification, communicate proactively and clearly.  Provide context and specific details in your queries. **It's better to ask a question early than to spend time going down the wrong path.**
* **Learn and Adapt for Faster Iteration:**  Pay attention to feedback, learn from mistakes, and continuously improve your coding skills and understanding of the project.  **Focus on delivering correct results efficiently, iterating quickly based on feedback.**

**II. Task Breakdown and Execution:**

* **Task Understanding & Confirmation:**
    * **Request Clarification (Crucial):**  If a task description is ambiguous, ask specific questions to clarify the requirements, expected inputs, outputs, and any constraints. **Focus on understanding the "why" behind the task, not just the "what".**
    * **Confirm Understanding:** Before starting, briefly summarize your understanding of the task back to the user to ensure alignment.  Example: "So, if I understand correctly, you want me to [summarize task]?"
    * **Identify Dependencies:**  Determine if the task depends on other parts of the codebase or tasks.  Flag any dependencies or potential conflicts.
* **Coding Process:**
    * **Modular Approach:** Break down complex tasks into smaller, manageable modules or functions.
    * **Iterative Development (Key for Speed):**  Implement features in small, testable increments. Don't try to build everything at once. **Focus on getting a basic version working quickly, then iterate and improve based on feedback and testing.**
    * **Comments & Documentation:**  Write clear and concise comments explaining the purpose of code blocks, functions, and complex logic.  Update documentation as needed. **For important decisions or complex logic, add comments directly in the code to explain the reasoning (for future reference, including your own).**
    * **Error Handling:** Implement robust error handling to gracefully handle unexpected inputs or situations.
    * **Code Reviews (Self & User):**
        * **Self-Review:** Before submitting code, review it yourself for clarity, correctness, and adherence to these guidelines.
        * **User Review:** Be prepared to explain your code and answer questions during user reviews.
    * while updating code, be aware of existing helper modules and services available in the codebase, dont implement functionalities from scratch, if there's a module available, use it.
    * if you find that there is a case for redundency, create a new helper module and update it in existing code.
* **Testing & Validation:**
    * **Unit Tests:** Write unit tests to verify the functionality of individual components or functions.
    * **Integration Tests:**  Write integration tests to ensure different parts of the system work together correctly.
    * **Edge Cases & Boundary Conditions:** Test for edge cases, invalid inputs, and boundary conditions to ensure robustness, especially important in financial applications.
    * **Provide Test Results:**  Clearly communicate the test results and any identified issues. **Focus on providing clear and concise test results to facilitate quick feedback loops.**

**III. Collaboration & Communication Protocols:**

* **Preferred Communication Channel:** **Project Chat** (for general communication and questions). **Important decisions or reasoning should also be documented as comments within the code itself.**
* **Frequency of Updates:** **After completion of each sub-task.**
* **Reporting Issues & Blockers:**  Immediately report any issues, blockers, or unexpected problems encountered.  Provide details and context in the project chat.
* **Asking Questions (When in Doubt, Ask!):**
    * **When you are unsure about *any* aspect of the task, ask questions in the project chat.** This is crucial for efficient task execution.
    * Be specific and provide context when asking questions.
    * Include relevant code snippets or error messages.
    * Clearly state what you have already tried or investigated (if applicable).
* **Responding to Feedback:**  Actively consider and respond to feedback provided by the user in the project chat.  Ask clarifying questions if feedback is unclear.

**IV. Technical Considerations:**

* **Programming Languages & Frameworks:** Python, Streamlit
* **Version Control System:** Git (Branching strategies may be project-specific).
* **Development Environment Setup:**
    * **IDE:** VSCode is the primary IDE.
    * **Python Environment:** Use `uv pip` for package management instead of `pip`. Ensure virtual environments are used for each project.
* CI/CD: Use Github Actions to schedule periodic service runs.

**V. Continuous Improvement & Learning:**

* **Feedback Incorporation for Faster Iteration:** Actively incorporate feedback from the user to improve code quality and efficiency.  **Focus on learning from each iteration to improve speed and accuracy in subsequent tasks.**
* **Code Analysis & Best Practices:**  Utilize code analysis tools (linters, static analyzers) to identify potential issues and improve code quality.  Strive to learn and apply best practices, especially in security and performance within the financial domain.
* **Project-Specific Learning:**  Continuously learn about the specific domain and requirements of the [Project Name] project and the financial context.

**VI.  Specific Task Type Guidelines:**

* **Feature Implementation:**
    * **Understand the feature's purpose and how it fits into the overall project goals.**
    * **Break down the feature into smaller, manageable sub-tasks.**
    * **Start with a basic implementation and iteratively add complexity.**
    * **Write unit tests for each component of the feature.**
    * **Consider potential edge cases and error conditions.**
    * **Document the feature's functionality and usage.**
* **Bug Fixing:**
    * **Thoroughly understand the bug report and try to reproduce the bug.**
    * **Isolate the root cause of the bug.**
    * **Write a test case that reproduces the bug before fixing it (regression test).**
    * **Implement the fix and verify that the test case now passes.**
    * **Ensure the fix doesn't introduce new regressions by running existing tests.**
    * **Document the bug and the fix in the Agent's Project Log (Section VIII).**
* **Refactoring:**
    * **Understand the reasons for refactoring (e.g., improve readability, performance, maintainability).**
    * **Refactor incrementally, making small, testable changes.**
    * **Ensure existing functionality is preserved by running tests after each refactoring step.**
    * **Focus on improving code structure and clarity without changing behavior.**
    * **Document the refactoring changes if significant.**
* **Documentation:**
    * **Understand the target audience for the documentation (developers, users, etc.).**
    * **Use clear, concise, and consistent language.**
    * **Provide code examples and usage instructions where appropriate.**
    * **Keep documentation up-to-date with code changes.**
    * **Document public APIs and important internal logic.**
    * **Consider different forms of documentation (code comments, READMEs, dedicated documentation files).**
* **Streamlit Dashboard Development:**
    * **Focus on clear and effective data visualization.**
    * **Optimize for performance, especially when handling large datasets.**
    * **Ensure dashboards are user-friendly and intuitive to navigate.**
    * **Consider dashboard layout and responsiveness across different screen sizes.**
    * **Implement necessary user interactions and filtering capabilities.**
    * **Document the purpose and usage of the dashboard.**
* **Strategy Execution Analysis (Financial Domain):**
    * **Prioritize data accuracy and integrity.**
    * **Clearly document all assumptions and methodologies used in the analysis.**
    * **Validate analysis results thoroughly and cross-reference with reliable sources.**
    * **Pay attention to financial domain best practices and regulations.**
    * **Present analysis results in a clear and understandable format.**
    * **Document data sources and data cleaning steps.**

**VII.  Important Notes & Reminders:**

* **Financial Domain Context:**  Remember that this project is in the financial domain.  **Pay very close attention to data security, accuracy, and performance.**  Validate results rigorously.
* **Iterative Development is Key:**  Focus on small, testable increments and frequent feedback to improve speed and reduce errors.
* **Ask Questions!:** When in doubt, always ask for clarification in the project chat.  Clear communication is essential for success.
* **Use `uv pip` for Python Package Management.**
* **Maintain the Agent's Project Log (Section VIII) diligently.**

**VIII. Agent's Project Log (For Agent's Internal Use):**

* **Purpose:** This log is for the agent's internal use to track project-specific information, decisions, issues, and resolutions.  It serves as a memory aid and helps in consistent decision-making and problem-solving over time.
* **Content to Log:**
    * **Decision Log:**  Record significant decisions made during development, especially when there were multiple options considered.  Document the reasoning behind the chosen approach.  *(Example: "Decision made to use library X for data processing because of its performance benefits, despite slightly steeper learning curve. Alternatives considered were Y and Z, but X was chosen for long-term scalability.")*
    * **Bug/Issue Log:**  When encountering bugs or issues (even if you resolve them yourself), briefly log them, including:
        * A short description of the bug/issue.
        * Steps taken to diagnose the issue.
        * The solution implemented.
        * Link to relevant code changes (commit or file).
        * *(Example: "Bug: Incorrect calculation in function 'calculate_profit'. Diagnosed as off-by-one error in loop index. Fixed by adjusting loop range. See commit [commit hash].")*
    * **Learning Log:**  Record any new things learned about the project, libraries, or domain that might be useful in the future. *(Example: "Learned that API endpoint /data/v2 is deprecated and should use /data/v3 instead. Updated code accordingly.")*
    * **"Gotchas" and Reminders:**  Note down any project-specific "gotchas" or recurring issues to avoid in the future.  *(Example: "Reminder: Project uses UTC timezone for all timestamps. Ensure all time-related calculations are timezone-aware.")*
* **Format:**  Use a simple and easily searchable format (e.g., plain text file, Markdown file) within the project directory. **This log is for your own benefit and should be maintained in a way that is most helpful to you.**

* **Storage Location:**  **Store the Agent's Project Log as a file named `agent_project_log.md` in the root directory of the project repository.**  This ensures it is easily accessible within the project context and can be version controlled along with the code.
* **Organization:** Organize entries within `agent_project_log.md` by date and category (Decision, Bug, Learning, Reminder) for better readability and searchability. get the present date using `date` bash command. Using Markdown formatting (headings, lists, code blocks) can also improve organization.


- avoid monolithic functions, create smaller modular functions