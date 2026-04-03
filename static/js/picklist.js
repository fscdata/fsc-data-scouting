document.addEventListener('DOMContentLoaded', function() {

    function storePickList() {
        const pickedTeams = [
            ...document.querySelectorAll('#picked-teams tr')
        ].filter(row => row.cells[0] && row.cells[0].textContent) // Skip header rows
         .map(row => {
            return {
                team: row.cells[0].textContent.trim()
            };
        });
        localStorage.setItem('pickedTeams', JSON.stringify(pickedTeams));
    }

    function setupAddButton(btn) {
        btn.addEventListener('click', function() {
            const row = this.closest('tr');
            const pickedTable = document.querySelector('#picked-teams');
            const newRow = document.createElement('tr');
            
            // Copy over data cells
            for(let i = 0; i < 9; i++) {
                const td = document.createElement('td');
                td.innerHTML = row.cells[i].innerHTML;
                newRow.appendChild(td);
            }
            
            // Add remove button
            const removeTd = document.createElement('td');
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-btn';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', removeFromPicked);
            removeTd.appendChild(removeBtn);
            newRow.appendChild(removeTd);
            
            pickedTable.appendChild(newRow);
            row.remove();
            storePickList();
        });
    }

    function removeFromPicked() {
        const row = this.closest('tr');
        const statsTable = document.querySelector('table:not(#picked-teams)');
        const newRow = document.createElement('tr');
        
        // Copy over data cells
        for(let i = 0; i < 9; i++) {
            const td = document.createElement('td');
            td.innerHTML = row.cells[i].innerHTML;
            newRow.appendChild(td);
        }
        
        // Add Add button
        const addTd = document.createElement('td');
        const addBtn = document.createElement('button');
        addBtn.className = 'add-btn';
        addBtn.textContent = 'Add';
        setupAddButton(addBtn);
        addTd.appendChild(addBtn);
        newRow.appendChild(addTd);
        
        statsTable.appendChild(newRow);
        row.remove();
        storePickList();
    }

    function loadPickList() {
        const pickedTeams = JSON.parse(localStorage.getItem('pickedTeams') || '[]');
        
        if (pickedTeams.length === 0) return;
        
        pickedTeams.forEach(pickedTeam => {
            // Find the Add button for this team and click it
            const teamNumberToFind = pickedTeam.team.trim();
            const buttons = document.querySelectorAll('table:not(#picked-teams) .add-btn');
            
            buttons.forEach(btn => {
                const row = btn.closest('tr');
                const teamNumber = row.cells[0].textContent.trim();
                
                if (teamNumber === teamNumberToFind) {
                    btn.click(); // Simulate clicking the Add button
                }
            });
        });
    }

    // Attach event listeners to existing buttons first
    document.querySelectorAll('.add-btn').forEach(btn => {
        setupAddButton(btn);
    });
    
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', removeFromPicked);
    });
    
    // Load picked teams from localStorage after event listeners are ready
    loadPickList();
});

