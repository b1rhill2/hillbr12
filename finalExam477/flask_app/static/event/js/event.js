document.addEventListener('DOMContentLoaded', function() {
     console.log('othersAvailabilityData content on load:',
    document.getElementById('othersAvailabilityData')?.textContent || 'Not found');
    // Track user interactions to prevent reloading during active use
    window.lastInteractionTime = Date.now();
    window.waitingForDataRefresh = false;

    // Add event listeners to track user interactions
    document.addEventListener('click', function () {
        window.lastInteractionTime = Date.now();
    });

    document.addEventListener('mousemove', function () {
        // Only update the time every second to avoid excessive updates
        const now = Date.now();
        if (now - window.lastInteractionTime > 1000) {
            window.lastInteractionTime = now;
        }
    });
    console.log('DOMContentLoaded: Page loaded');

    const availabilityModeSelect = document.getElementById('availabilityMode');
    const selectedModeDisplay = document.getElementById('selectedMode');
    const availabilityCells = document.querySelectorAll('.availability-cell');

    // Get the event ID from the URL
    const eventId = window.location.pathname.split('/').pop();
    console.log('Event ID from URL:', eventId);

    // Store current user information
    const currentUserEmail = document.querySelector('meta[name="user-email"]')?.content;
    const currentUserId = document.querySelector('meta[name="user-id"]')?.content;
    console.log('Current user:', currentUserEmail, '(ID:', currentUserId, ')');

    let currentMode = availabilityModeSelect.value;
    console.log('Initial currentMode:', currentMode);
    selectedModeDisplay.textContent = currentMode.charAt(0).toUpperCase() + currentMode.slice(1);
    selectedModeDisplay.className = 'selected-mode ' + currentMode;

    // Track changed cells for batch saving
    let changedCells = new Set();
    console.log('changedCells initialized:', changedCells);

    //Color and status of selection
    availabilityModeSelect.addEventListener('change', function () {
        currentMode = this.value;
        console.log('availabilityModeSelect changed, currentMode:', currentMode);
        selectedModeDisplay.textContent = currentMode.charAt(0).toUpperCase() + currentMode.slice(1);
        selectedModeDisplay.className = 'selected-mode ' + currentMode;
    });

    //----------------------------------------------------
    //              Table interaction
    //----------------------------------------------------

    let isDragging = false;
    let startCell = null;


    availabilityCells.forEach(cell => {
        cell.addEventListener('mousedown', function (e) {
            console.log('mousedown on cell:', this);
            isDragging = true;
            startCell = this;
            applyAvailability(this, currentMode);
            e.preventDefault(); // Prevent text selection during drag
        });

        cell.addEventListener('mouseover', function () {
            if (isDragging && this !== startCell) {
                console.log('mouseover on cell during drag:', this);
                applyAvailability(this, currentMode);
            }
        });

        cell.addEventListener('mouseup', function () {
            if (isDragging) {
                console.log('mouseup on cell after drag/click');
                isDragging = false;
                startCell = null;
                // Persist all changed cells in a batch
                if (changedCells.size > 0) {
                    const cellsToSave = Array.from(changedCells);
                    console.log('Cells to save:', cellsToSave);
                    saveAvailabilityBatch(cellsToSave);
                    changedCells.clear();
                    console.log('changedCells cleared:', changedCells);
                }
            }
        });

        cell.addEventListener('mouseleave', function (e) {
            if (isDragging && e.buttons === 0) { // Stop dragging if mouse leaves while button is up
                console.log('mouseleave on cell during drag (button up):', this);
                isDragging = false;
                startCell = null;
                // Persist all changed cells in a batch
                if (changedCells.size > 0) {
                    const cellsToSave = Array.from(changedCells);
                    console.log('Cells to save on mouseleave (button up):', cellsToSave);
                    saveAvailabilityBatch(cellsToSave);
                    changedCells.clear();
                    console.log('changedCells cleared on mouseleave (button up):', changedCells);
                }
            }
        });

        cell.addEventListener('dragstart', function (e) {
            console.log('dragstart prevented on cell:', this);
            e.preventDefault(); // Prevent default drag behavior
        });
    });

    document.addEventListener('mouseup', function () {
        if (isDragging) {
            console.log('mouseup on document during drag');
            isDragging = false;
            startCell = null;
            // Persist all changed cells in a batch
            if (changedCells.size > 0) {
                const cellsToSave = Array.from(changedCells);
                console.log('Cells to save on document mouseup:', cellsToSave);
                saveAvailabilityBatch(cellsToSave);
                changedCells.clear();
                console.log('changedCells cleared on document mouseup:', changedCells);
            }
        }
    });


    //----------------------------------------------------
    //              Heat Map
    //----------------------------------------------------

    function applyAvailability(cell, mode) {
        console.log('applyAvailability called on cell:', cell, 'with mode:', mode);

        // Store the current user's selection
        cell.dataset.userAvailability = mode;

        // Add this cell to the batch of changes
        const cellData = {
            date: cell.dataset.date,
            startTime: cell.dataset.startTime,
            endTime: cell.dataset.endTime,
            availability: mode
        };
        changedCells.add(JSON.stringify(cellData));
        console.log('changedCells after applyAvailability:', changedCells);

        // Update the heatmap immediately for a responsive feel
        // We'll make a working copy of the participant data and add our temporary change to it
        if (currentUserId) {
            // Make a copy of the current participant data (or initialize if undefined)
            const tempParticipantData = window.participantAvailability ?
                [...window.participantAvailability] : [];

            // Find if the current user already has an entry for this timeslot
            const existingEntryIndex = tempParticipantData.findIndex(item =>
                item.user_id == currentUserId &&
                item.date === cellData.date &&
                item.start_time === cellData.startTime &&
                item.end_time === cellData.endTime
            );

            if (existingEntryIndex >= 0) {
                // Update the existing entry
                tempParticipantData[existingEntryIndex].availability = mode;
            } else {
                // Add a new temporary entry
                tempParticipantData.push({
                    user_id: currentUserId,
                    email: currentUserEmail,
                    date: cellData.date,
                    start_time: cellData.startTime,
                    end_time: cellData.endTime,
                    availability: mode
                });
            }

            // Store the temporary data and update the heatmap
            window.tempParticipantData = tempParticipantData;
            updateHeatmap(tempParticipantData);
        } else {
            // If we can't identify the current user, just update directly
            updateHeatmap();
        }
    }

    function updateHeatmap(participantData) {
        // Use provided participant data or fall back to the global data
        const dataToUse = participantData || window.participantAvailability;
        if (!dataToUse) return;

        // Process each cell to update its appearance based on the heatmap data
        availabilityCells.forEach(cell => {
            const date = cell.dataset.date;
            const startTime = cell.dataset.startTime;
            const endTime = cell.dataset.endTime;

            // Get the current user's status for this cell
            const userStatus = cell.dataset.userAvailability || 'none';

            // Count the statuses for this timeslot using the provided data
            const availableCount = countParticipantsWithStatus(date, startTime, endTime, 'available', dataToUse);
            const maybeCount = countParticipantsWithStatus(date, startTime, endTime, 'maybe', dataToUse);
            const unavailableCount = countParticipantsWithStatus(date, startTime, endTime, 'unavailable', dataToUse);
            const totalCount = availableCount + maybeCount + unavailableCount;

            // Reset all classes except the base class
            cell.className = 'availability-cell';

            // Add the user's own status class
            if (userStatus !== 'none') {
                cell.classList.add(userStatus);
            }

            // Apply heatmap classes based on the availability counts
            if (availableCount > 0) {
                // Available has priority - apply intensity based on count
                if (availableCount === 1) {
                    cell.classList.add('heatmap-available-1');
                } else if (availableCount === 2) {
                    cell.classList.add('heatmap-available-2');
                } else if (availableCount === 3) {
                    cell.classList.add('heatmap-available-3');
                } else if (availableCount === 4) {
                    cell.classList.add('heatmap-available-4');
                } else {
                    cell.classList.add('heatmap-available-many');
                }
            } else if (maybeCount > 0) {
                // Maybe is next priority
                cell.classList.add('heatmap-maybe');
            } else if (unavailableCount > 0) {
                // Unavailable has lowest priority
                cell.classList.add('heatmap-unavailable');
            }

            // Add a counter element if there are participants
            if (totalCount > 0) {
                // Remove any existing counter
                const existingCounter = cell.querySelector('.counter');
                if (existingCounter) {
                    cell.removeChild(existingCounter);
                }

                // Add a new counter
                const counter = document.createElement('span');
                counter.className = 'counter';
                counter.textContent = availableCount;
                cell.appendChild(counter);

                // Set tooltip with detailed counts
                cell.title = `Available: ${availableCount}, Maybe: ${maybeCount}, Unavailable: ${unavailableCount}`;
            } else {
                // Remove counter if no participants
                const existingCounter = cell.querySelector('.counter');
                if (existingCounter) {
                    cell.removeChild(existingCounter);
                }
                cell.removeAttribute('title');
            }
        });
    }

    function countParticipantsWithStatus(date, startTime, endTime, status, participantData) {
        // Use the provided participant data or fall back to the global data
        const dataToUse = participantData || window.participantAvailability;
        if (!dataToUse) return 0;

        return dataToUse.filter(item =>
            item.date === date &&
            item.start_time === startTime &&
            item.end_time === endTime &&
            item.availability === status
        ).length;
    }

    //----------------------------------------------------
    //     Best time calculation
    //----------------------------------------------------

        // Function to calculate the best time to meet
    function calculateBestTimeToMeet(participantData) {
        // Guard against invalid data
        if (!participantData || !Array.isArray(participantData) || participantData.length === 0) {
            return { status: 'no-data', message: 'No availability submitted yet' };
        }

        // Get unique time slots from the data
        const timeSlots = new Map();

        participantData.forEach(item => {
            const slotKey = `${item.date}|${item.start_time}|${item.end_time}`;

            if (!timeSlots.has(slotKey)) {
                timeSlots.set(slotKey, {
                    date: item.date,
                    startTime: item.start_time,
                    endTime: item.end_time,
                    available: 0,
                    maybe: 0,
                    unavailable: 0,
                    users: new Set()
                });
            }

            const slot = timeSlots.get(slotKey);

            // Only count each user once per slot
            if (!slot.users.has(item.user_id)) {
                slot.users.add(item.user_id);

                if (item.availability === 'available') {
                    slot.available++;
                } else if (item.availability === 'maybe') {
                    slot.maybe++;
                } else if (item.availability === 'unavailable') {
                    slot.unavailable++;
                }
            }
        });

        // Convert Map to array for sorting
        const slotArray = Array.from(timeSlots.values());

        // Check if we have any availability data
        const hasAvailability = slotArray.some(slot => slot.available > 0);

        if (!hasAvailability) {
            // If no availability, get earliest slot
            slotArray.sort((a, b) => {
                // Compare dates
                const dateComparison = a.date.localeCompare(b.date);
                if (dateComparison !== 0) return dateComparison;

                // If dates are the same, compare start times
                return a.startTime.localeCompare(b.startTime);
            });

            if (slotArray.length > 0) {
                return {
                    status: 'no-availability',
                    bestSlot: slotArray[0],
                    message: 'No one is currently available. Showing earliest time slot.'
                };
            } else {
                return { status: 'no-data', message: 'No availability submitted yet' };
            }
        }

        // Sort the slots based on priority rules
        slotArray.sort((a, b) => {
            // Rule 1: Highest number of users marked as "Available"
            if (a.available !== b.available) {
                return b.available - a.available; // Descending
            }

            // Rule 2: Fewest users marked as "Unavailable"
            if (a.unavailable !== b.unavailable) {
                return a.unavailable - b.unavailable; // Ascending
            }

            // Rule 3: Earliest time slot
            // Compare dates
            const dateComparison = a.date.localeCompare(b.date);
            if (dateComparison !== 0) return dateComparison;

            // If dates are the same, compare start times
            return a.startTime.localeCompare(b.startTime);
        });

        // Return the best slot
        return {
            status: 'success',
            bestSlot: slotArray[0],
            message: 'Best time calculated based on availability'
        };
    }

    // Function to format date and time for display
    function formatDateTime(dateStr, timeStr) {
        // Parse the date
        const [year, month, day] = dateStr.split('-').map(Number);
        const date = new Date(year, month - 1, day);

        // Format the date (e.g., "Tuesday, April 16")
        const dateOptions = { weekday: 'long', month: 'long', day: 'numeric' };
        const formattedDate = date.toLocaleDateString('en-US', dateOptions);

        // Format the time (e.g., "2:00 PM")
        let [hours, minutes] = timeStr.split(':').map(Number);
        const period = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12; // Convert to 12-hour format
        const formattedTime = `${hours}:${minutes.toString().padStart(2, '0')} ${period}`;

        return { formattedDate, formattedTime };
    }

    // Function to add the "Best Time to Meet" section to the page
    function addBestTimeSection() {
        // Create the section container
        const bestTimeSection = document.createElement('div');
        bestTimeSection.className = 'best-time-section';
        bestTimeSection.innerHTML = `
            <h2>Best Time to Meet</h2>
            <div id="best-time-content" class="best-time-content">
                <p>Calculating best time...</p>
            </div>
        `;

            // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .best-time-section {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                max-width: 500px;
            }
            
            .best-time-section h2 {
                margin-top: 0;
                margin-bottom: 10px;
                color: #333;
            }
            
            .best-time-content {
                padding: 10px;
                background-color: white;
                border-radius: 4px;
                border-left: 4px solid #28a745;
            }
            
            .best-time-date {
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 5px;
            }
            
            .best-time-time {
                font-size: 16px;
                color: #555;
            }
            
            .best-time-stats {
                margin-top: 10px;
                font-size: 14px;
                color: #666;
            }
            
            .no-data-message {
                color: #666;
                font-style: italic;
            }
            
            .no-availability-message {
                color: #856404;
                background-color: #fff3cd;
                padding: 8px;
                border-radius: 4px;
                margin-top: 10px;
                font-size: 14px;
            }
        `;


             // Insert the section into the page
        const availabilityControls = document.querySelector('.availability-controls');
        if (availabilityControls) {
            availabilityControls.parentNode.insertBefore(bestTimeSection, availabilityControls.nextSibling);
            document.head.appendChild(style);
        } else {
            // Fallback: add to the top of the page
            const firstElement = document.body.firstChild;
            document.body.insertBefore(bestTimeSection, firstElement);
            document.head.appendChild(style);
        }
    }

    function updateBestTimeSection(bestTimeResult) {
    const bestTimeContent = document.getElementById('best-time-content');
    if (!bestTimeContent) return;

    if (bestTimeResult.status === 'no-data') {
        bestTimeContent.innerHTML = `
            <p class="no-data-message">${bestTimeResult.message}</p>
        `;
        return;
    }

    if (bestTimeResult.status === 'no-availability') {
        const { formattedDate, formattedTime } = formatDateTime(
            bestTimeResult.bestSlot.date,
            bestTimeResult.bestSlot.startTime
        );

        const endTimeFormatted = formatDateTime(
            bestTimeResult.bestSlot.date,
            bestTimeResult.bestSlot.endTime
        ).formattedTime;

        bestTimeContent.innerHTML = `
            <p class="best-time-date">${formattedDate}</p>
            <p class="best-time-time">${formattedTime} – ${endTimeFormatted}</p>
            <p class="no-availability-message">${bestTimeResult.message}</p>
        `;
        return;
    }

    // Format the date and time
    const { formattedDate, formattedTime } = formatDateTime(
        bestTimeResult.bestSlot.date,
        bestTimeResult.bestSlot.startTime
    );

    const endTimeFormatted = formatDateTime(
        bestTimeResult.bestSlot.date,
        bestTimeResult.bestSlot.endTime
    ).formattedTime;

    // Create the content
    bestTimeContent.innerHTML = `
        <p class="best-time-date">${formattedDate}</p>
        <p class="best-time-time">${formattedTime} – ${endTimeFormatted}</p>
        <p class="best-time-stats">
            ${bestTimeResult.bestSlot.available} people available
            ${bestTimeResult.bestSlot.maybe > 0 ? `, ${bestTimeResult.bestSlot.maybe} maybe` : ''}
            ${bestTimeResult.bestSlot.unavailable > 0 ? `, ${bestTimeResult.bestSlot.unavailable} unavailable` : ''}
        </p>
    `;
}


    // Function to update the "Best Time to Meet" section with the calculated best time

    //----------------------------------------------------
    //      Utility function to show a toast message
    //----------------------------------------------------

    function showToast(message, type = 'error', duration = 3000) {
        // Create toast element if it doesn't exist
        let toast = document.getElementById('availability-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'availability-toast';
            document.body.appendChild(toast);
        }

        // Clear any existing classes and add the new type
        toast.className = '';
        toast.classList.add(type); // 'error', 'info', or 'success'

        // Set message and show toast
        toast.textContent = message;
        toast.style.display = 'block';

        // Hide after specified duration
        clearTimeout(window.toastTimeout);
        window.toastTimeout = setTimeout(() => {
            toast.style.display = 'none';
        }, duration);
    }

    // Add this somewhere in your script

// Helper function to inspect data
    function debugInspectData() {
        console.group('Debug Data Inspection');

        console.log('othersAvailabilityData element:', document.getElementById('othersAvailabilityData'));
        console.log('othersAvailabilityData content:', document.getElementById('othersAvailabilityData')?.textContent || 'Not found');

        try {
            const content = document.getElementById('othersAvailabilityData')?.textContent;
            if (content && content.trim() !== '') {
                const parsed = JSON.parse(content);
                console.log('Parsed data:', parsed);
                console.log('Data is array:', Array.isArray(parsed));
                console.log('Data length:', parsed.length);
            } else {
                console.log('No content to parse');
            }
        } catch (e) {
            console.error('Error parsing content:', e);
        }

        console.log('Global participantAvailability:', window.participantAvailability);
        console.log('Global tempParticipantData:', window.tempParticipantData);
        console.log('Current User ID:', currentUserId);

        console.groupEnd();
    }

    // Add button to manually trigger data load for debugging
    function addDebugControls() {
        const controls = document.createElement('div');
        controls.style.position = 'fixed';
        controls.style.top = '10px';
        controls.style.right = '10px';
        controls.style.zIndex = '9999';
        controls.style.backgroundColor = '#f0f0f0';
        controls.style.padding = '5px';
        controls.style.borderRadius = '5px';
        controls.style.border = '1px solid #ccc';

        const inspectBtn = document.createElement('button');
        inspectBtn.textContent = 'Inspect Data';
        inspectBtn.onclick = debugInspectData;
        controls.appendChild(inspectBtn);

        const loadBtn = document.createElement('button');
        loadBtn.textContent = 'Reload Data';
        loadBtn.onclick = function() {
            loadParticipantsAvailability();
        };
        controls.appendChild(loadBtn);

        document.body.appendChild(controls);
    }


    //-------------------------------------------------------------------------
    //          Save Load, and Process User availability functions
    //-------------------------------------------------------------------------

    // save all availability data when the page loads
    function saveAvailabilityBatch(cellsDataStrings) {
        // Convert stringified objects back to objects
        const cellsData = Array.from(cellsDataStrings).map(dataString => JSON.parse(dataString));

        // Don't send empty data
        if (cellsData.length === 0) {
            console.log('No changes to save');
            return;
        }

        console.log('saveAvailabilityBatch called with data:', cellsData);

        // Capture the temporary data for continued use
        const tempData = window.tempParticipantData ? [...window.tempParticipantData] : null;

        // Add a "saving" indicator to the affected cells
        cellsData.forEach(item => {
            const cellSelector = `.availability-cell[data-date="${item.date}"][data-start-time="${item.startTime}"][data-end-time="${item.endTime}"]`;
            const cell = document.querySelector(cellSelector);
            if (cell) {
                cell.classList.add('saving');
            }
        });

        // Retry logic variables
        const maxRetries = 3;
        let retryCount = 0;

        function attemptSave() {
            $.ajax({
                url: '/save-availability',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    eventId: eventId,
                    availabilityData: cellsData
                }),
                success: function (response) {
                    console.log('AJAX success - Availability saved successfully:', response);
                    const bestTimeResult = calculateBestTimeToMeet(tempData || window.participantAvailability);
                    updateBestTimeSection(bestTimeResult);

                    // Remove saving indicator from cells
                    cellsData.forEach(item => {
                        const cellSelector = `.availability-cell[data-date="${item.date}"][data-start-time="${item.startTime}"][data-end-time="${item.endTime}"]`;
                        const cell = document.querySelector(cellSelector);
                        if (cell) {
                            cell.classList.remove('saving');
                            // Add a brief success indicator
                            cell.classList.add('save-success');
                            setTimeout(() => {
                                cell.classList.remove('save-success');
                            }, 1000);
                        }
                    });

                    // Show success toast
                    showToast("Availability saved successfully!", "success", 1500);

                    // IMPORTANT: Instead of reloading participant data immediately,
                    // keep using the temporary data we have and MERGE the server response
                    // into it when it arrives after a significant delay

                    // Set a flag to indicate we're waiting for a fresh data load
                    window.waitingForDataRefresh = true;

                    // Only trigger a reload after a significant delay (5 seconds)
                    // to ensure server has time to process and for users to continue interactions
                    setTimeout(() => {
                        // Only reload if no interactions have happened in the last 5 seconds
                        if (Date.now() - window.lastInteractionTime > 5000) {
                            loadParticipantsAvailability(true); // true = silent reload
                        }
                    }, 5000);
                },
                error: function (xhr, status, error) {
                    console.error(`AJAX error - Error saving availability (attempt ${retryCount + 1}/${maxRetries}):`, error);

                    try {
                        // Try to parse the response
                        const response = JSON.parse(xhr.responseText);
                        console.log('AJAX error response:', response);
                    } catch (e) {
                        console.log('AJAX error response (raw):', xhr.responseText);
                    }

                    // Check if we should retry
                    if (retryCount < maxRetries &&
                        (xhr.status === 500 || xhr.status === 429 || xhr.status === 0)) {
                        retryCount++;

                        // Exponential backoff
                        const backoffDelay = 1000 * Math.pow(2, retryCount - 1);
                        console.log(`Retrying save in ${backoffDelay}ms...`);

                        showToast(`Save failed. Retrying in ${backoffDelay / 1000} seconds... (${retryCount}/${maxRetries})`, "error");

                        setTimeout(attemptSave, backoffDelay);
                    } else {
                        // No more retries or non-retryable error
                        console.log('Max retries reached or non-retryable error');

                        // Remove saving indicator from cells
                        cellsData.forEach(item => {
                            const cellSelector = `.availability-cell[data-date="${item.date}"][data-start-time="${item.startTime}"][data-end-time="${item.endTime}"]`;
                            const cell = document.querySelector(cellSelector);
                            if (cell) {
                                cell.classList.remove('saving');
                                cell.classList.add('save-error');

                                // Remove error class after 3 seconds
                                setTimeout(() => {
                                    cell.classList.remove('save-error');
                                }, 3000);
                            }
                        });

                        // If there was an error, we should keep using the temporary data
                        if (tempData) {
                            window.tempParticipantData = tempData;
                            updateHeatmap(tempData);
                        }

                        // Show an error message
                        showToast("Error saving your availability. Changes will be visible to you but not saved.", "error");
                    }
                }
            });
        }

        // Track last interaction time
        window.lastInteractionTime = Date.now();

        // Start the first attempt
        attemptSave();
    }


// Load all availability data when the page loads
    function loadParticipantsAvailability(silentReload = false) {
        // Show loading indicator for initial load only
        const isInitialLoad = !window.participantAvailability;
        if (isInitialLoad && !silentReload) {
            showLoading();
        }

        // Preserve our temporary data if it exists
        const tempDataBeforeLoad = window.tempParticipantData ? [...window.tempParticipantData] : null;

        const othersAvailElement = document.getElementById('othersAvailabilityData');

        // Debug output for initial load
        if (isInitialLoad) {
            console.log('Initial page load - checking for embedded data');
            console.log('othersAvailElement:', othersAvailElement);
            if (othersAvailElement) {
                console.log('othersAvailElement content:', othersAvailElement.textContent);
            }
        }

        // Check if we have inline data on initial load
        if (othersAvailElement && othersAvailElement.textContent && othersAvailElement.textContent.trim() !== '') {
            console.log('Inline participant availability data found');
            try {
                const participantsData = JSON.parse(othersAvailElement.textContent);
                console.log('Parsed inline data:', participantsData);
                processParticipantData(participantsData, tempDataBeforeLoad, silentReload);
                if (isInitialLoad && !silentReload) {
                    hideLoading();
                }
            } catch (e) {
                console.error('Error parsing participant availability data:', e);
                if (isInitialLoad && !silentReload) {
                    hideLoading();
                }
                // Fall back to AJAX if parsing fails
                loadViaAjax();
            }
        } else {
            // No inline data, use AJAX
            console.log('No inline data found, loading via AJAX');
            loadViaAjax();
        }

        // Helper function to load via AJAX to avoid duplicate code
        function loadViaAjax() {
            $.ajax({
                url: '/get-all-availability',
                type: 'GET',
                data: {eventId: eventId},
                success: function (data) {
                    if (silentReload) {
                        console.log('Silent reload - All participants availability data loaded');
                    } else {
                        console.log('AJAX success - All participants availability data loaded:', data);
                    }

                    if (data && data.availabilityData) {
                        console.log('Received data via AJAX:', data.availabilityData);
                        processParticipantData(data.availabilityData, tempDataBeforeLoad, silentReload);
                    } else {
                        console.warn('AJAX response contained no availability data');
                    }

                    if (isInitialLoad && !silentReload) {
                        hideLoading();
                    }

                    if (data && data.availabilityData) {
                        const bestTimeResult = calculateBestTimeToMeet(data.availabilityData);
                        updateBestTimeSection(bestTimeResult);
                    }

                    // Clear the waiting flag
                    window.waitingForDataRefresh = false;
                },
                error: function (xhr, status, error) {
                    console.error('AJAX error - Error loading participants availability data:', error);
                    console.log('AJAX error status:', status);
                    console.log('AJAX error response:', xhr.responseText);

                    // If we have temporary data, keep using it
                    if (tempDataBeforeLoad) {
                        window.tempParticipantData = tempDataBeforeLoad;
                        updateHeatmap(tempDataBeforeLoad);
                    }

                    if (isInitialLoad && !silentReload) {
                        hideLoading();
                        // Show error toast on initial load failure
                        showToast("Failed to load availability data. Please refresh the page.", "error");
                    }

                    // Clear the waiting flag
                    window.waitingForDataRefresh = false;
                }
            });
        }
    }

    function processParticipantData(participantsData, tempDataBeforeLoad = null, silentReload = false) {
        // Guard against empty or invalid data
        if (!participantsData || !Array.isArray(participantsData)) {
            console.error('Invalid participant data received:', participantsData);
            return;
        }

        if (participantsData.length === 0) {
            console.log('Empty participant data received. No availability to display.');

            // For initial load, still update the UI to show empty state
            if (!window.participantAvailability) {
                // const bestTimeResult = calculateBestTimeToMeet(window.participantAvailability);
                // updateBestTimeSection(bestTimeResult);
                window.participantAvailability = [];
                updateHeatmap([]);
            }

            return;
        }

        if (silentReload) {
            console.log('Silent processing of participant data');
        } else {
            console.log('Processing participant data:', participantsData);
        }

        // Store all participant data globally
        window.participantAvailability = participantsData;

        // If we had temporary data before, we need to decide what to do with it
        if (tempDataBeforeLoad && window.waitingForDataRefresh) {
            console.log('Merging temporary data with new server data');

            // Find all cells that had temporary changes
            const temporaryChanges = [];

            // For each user-modified cell in the temp data
            if (currentUserId) {
                const currentUserTempData = tempDataBeforeLoad.filter(item => item.user_id == currentUserId);

                // Extract the user's changes from temp data
                currentUserTempData.forEach(tempItem => {
                    // Check if this item exists in the new server data
                    const existsInNewData = participantsData.some(
                        item => item.user_id == currentUserId &&
                            item.date === tempItem.date &&
                            item.start_time === tempItem.start_time &&
                            item.end_time === tempItem.end_time &&
                            item.availability === tempItem.availability
                    );

                    // If it doesn't exist in the new data, it's a change that hasn't been saved yet
                    if (!existsInNewData) {
                        temporaryChanges.push(tempItem);
                    }
                });
            }

            // If we found temporary changes that aren't reflected in the server data yet
            if (temporaryChanges.length > 0) {
                console.log('Found temporary changes not yet in server data:', temporaryChanges);

                // Create a new combined data set
                const combinedData = [...participantsData];

                // For each temporary change
                temporaryChanges.forEach(tempItem => {
                    // Check if there's an existing entry to update
                    const existingIndex = combinedData.findIndex(
                        item => item.user_id == tempItem.user_id &&
                            item.date === tempItem.date &&
                            item.start_time === tempItem.start_time &&
                            item.end_time === tempItem.end_time
                    );

                    if (existingIndex >= 0) {
                        // Update the existing entry
                        combinedData[existingIndex].availability = tempItem.availability;
                    } else {
                        // Add as a new entry
                        combinedData.push(tempItem);
                    }
                });

                // Use this combined data instead
                window.participantAvailability = combinedData;
                window.tempParticipantData = combinedData;

                // If we're doing this silently, show a gentle notification
                if (silentReload) {
                    showToast("Updated with others' changes while preserving yours", "info", 2000);
                }
            } else {
                // No temporary changes to preserve, clear temp data
                window.tempParticipantData = null;
            }
        } else {
            // No temporary data to preserve
            window.tempParticipantData = null;
        }

        // Extract current user's availability
        let currentUserData = [];
        if (currentUserId) {
            currentUserData = window.participantAvailability.filter(item => item.user_id == currentUserId);
            if (!silentReload) {
                console.log('Current user data extracted:', currentUserData);
            }
        } else if (currentUserEmail) {
            currentUserData = window.participantAvailability.filter(item => item.email === currentUserEmail);
            if (!silentReload) {
                console.log('Current user data extracted by email:', currentUserData);
            }
        }

        // Clear all cells' user availability status first
        availabilityCells.forEach(cell => {
            delete cell.dataset.userAvailability;
        });

        // Apply the current user's availability to cells
        currentUserData.forEach(item => {
            const cellSelector = `.availability-cell[data-date="${item.date}"][data-start-time="${item.start_time}"][data-end-time="${item.end_time}"]`;
            const cell = document.querySelector(cellSelector);
            if (cell) {
                if (!silentReload) {
                    console.log('Found cell for current user:', cellSelector, 'setting availability to:', item.availability);
                }
                cell.dataset.userAvailability = item.availability;
            } else if (!silentReload) {
                console.warn('Cell not found for current user item:', item);
            }
        });
        const bestTimeResult = calculateBestTimeToMeet(window.participantAvailability);
        updateBestTimeSection(bestTimeResult);
        // Update the heatmap with all participant data
        updateHeatmap(window.participantAvailability);
    }

    // Initialize everything
    loadParticipantsAvailability();
    addBestTimeSection();

    // Only enable in development environment
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        addDebugControls();
        // Debug on initial load
        setTimeout(debugInspectData, 1000);
    }


        function showLoading() {
        // Implementation might be missing
        console.log("Loading data...");
    }

    function hideLoading() {
        // Implementation might be missing
        console.log("Loading complete");
    }

});