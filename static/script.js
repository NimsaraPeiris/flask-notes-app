document.addEventListener('DOMContentLoaded', function() {
    const kanbanColumns = ['todo', 'ongoing', 'completed'];
    
    // Fetch tasks from the backend and populate the Kanban board
    function loadTasks() {
        fetch('/get_tasks')  // Route to fetch tasks (to be added in Flask)
            .then(response => response.json())
            .then(data => {
                kanbanColumns.forEach(status => {
                    const column = document.getElementById(`${status}-tasks`);
                    column.innerHTML = '';  // Clear column
                    data.tasks.filter(task => task.status === status).forEach(task => {
                        const taskElement = document.createElement('li');
                        taskElement.textContent = task.title;
                        taskElement.draggable = true;
                        taskElement.addEventListener('dragstart', function(e) {
                            e.dataTransfer.setData('task_id', task.id);
                            e.dataTransfer.setData('new_status', status);
                        });
                        column.appendChild(taskElement);
                    });
                });
            });
    }

    // Handle dropping tasks into different columns
    kanbanColumns.forEach(status => {
        const column = document.getElementById(`${status}-column`);
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
        });
        column.addEventListener('drop', function(e) {
            e.preventDefault();
            const taskId = e.dataTransfer.getData('task_id');
            const newStatus = e.dataTransfer.getData('new_status');
            
            // Only update if the status changes
            if (newStatus !== status) {
                fetch(`/update_task_status/${taskId}/${status}`, { method: 'POST' })
                    .then(loadTasks);  // Refresh tasks after update
            }
        });
    });

    loadTasks();  // Initial load of tasks
});