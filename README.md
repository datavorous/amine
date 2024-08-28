# amine 

<img src="demo.png" width="80%">

### Why this? Well, popular website blockers are not equipped enough, willpower can't be trusted, Cold Turkey ain't got so much flexibilty, and i need to pass my exams.

### **1. Working Mechanism**

**Amine** is a Flask-based application that combines a Pomodoro timer with advanced distraction-blocking techniques. The application allows users to define work sessions (Pomodoros) and breaks while enforcing focus by restricting certain keys and preventing the mouse from accessing certain screen areas. This ensures the user remains undistracted during their focus sessions.

### **2. Logic Handling**

#### **a. Pomodoro Timer Logic:**
- **Pomodoro Sessions**: The user can configure the number of Pomodoros, focus duration, break duration, and the target website to open during the session.
- **Flow Execution**: The Pomodoro flow is handled by the `pomodoro_flow` function, which launches a new thread for the session and handles the sequence of Pomodoro sessions and breaks.

#### **b. Focus Protection Logic:**
- **Distraction Blocking**: A `FocusProtection` class is responsible for enforcing focus by blocking specific keys and restricting mouse movement.
- **Key Blocking**: All keys listed in the `CONFIG["BLOCKED_KEYS"]` array are blocked during focus sessions using the `keyboard` module.
- **Mouse Boundaries**: The `enforce_mouse_boundaries` method ensures the mouse cursor stays away from screen edges where potential distractions (like tabs or taskbars) could reside. If the mouse crosses the defined `TOP_SCREEN_THRESHOLD`, it is moved back to a safe position.

### **3. Threading and Concurrent Execution**

- **Threading for Concurrent Tasks**: The application uses Python's `threading` module to manage concurrent tasks, such as running the Pomodoro timer and enforcing focus protection simultaneously. This ensures that while the main timer is running, the distraction-blocking measures are active.
  
- **Daemon Threads**: The mouse boundary enforcement runs on a daemon thread, meaning it runs in the background and stops automatically when the main program exits.

### **4. Clever Mechanisms and Design Decisions**

- **Exit Combo for Safety**: The application allows users to exit the focus session early using a configurable keyboard shortcut (`ctrl+shift+q`). This combo is constantly checked during focus sessions to allow a quick escape without needing to modify the code.

- **Window Management**: The application automatically minimizes the Flask window when a Pomodoro session starts and restores it after all Pomodoros are completed. This minimizes distractions and brings the user back to the application's interface when the session ends.

- **Mouse Enforcement with Adjustable Delay**: The mouse enforcement delay is configurable (`MOUSE_ENFORCE_DELAY`), allowing for smoother or stricter control over the mouse movement depending on user preferences.

### **5. Unique Features Compared to Other Blockers**

- **Integrated Pomodoro Timer**: Unlike other tools like Freedom or RescueTime, Amine integrates a Pomodoro timer with distraction blocking, offering a seamless experience for users who follow the Pomodoro technique.

- **Custom Key Blocking**: The app allows for precise control over which keys are blocked, ensuring that the user cannot open task managers, switch windows, or exit full-screen mode accidentally.

- **Mouse Boundary Enforcement**: Amine uniquely ensures that the user’s mouse stays away from potentially distracting screen areas, unlike most focus tools that only block websites or apps.


