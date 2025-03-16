document.addEventListener("DOMContentLoaded", function() {
    const piano = document.getElementById("piano");
    const white_key_notes = document.getElementsByClassName("white-key-note");
    const black_key_notes = document.getElementsByClassName("black-key-note");
    let dead = false;
    // Your JSON object containing keyCodes and corresponding sound URLs
    const sound = {
        65: "http://carolinegabriel.com/demo/js-keyboard/sounds/040.wav",
        87: "http://carolinegabriel.com/demo/js-keyboard/sounds/041.wav",
        83: "http://carolinegabriel.com/demo/js-keyboard/sounds/042.wav",
        69: "http://carolinegabriel.com/demo/js-keyboard/sounds/043.wav",
        68: "http://carolinegabriel.com/demo/js-keyboard/sounds/044.wav",
        70: "http://carolinegabriel.com/demo/js-keyboard/sounds/045.wav",
        84: "http://carolinegabriel.com/demo/js-keyboard/sounds/046.wav",
        71: "http://carolinegabriel.com/demo/js-keyboard/sounds/047.wav",
        89: "http://carolinegabriel.com/demo/js-keyboard/sounds/048.wav",
        72: "http://carolinegabriel.com/demo/js-keyboard/sounds/049.wav",
        85: "http://carolinegabriel.com/demo/js-keyboard/sounds/050.wav",
        74: "http://carolinegabriel.com/demo/js-keyboard/sounds/051.wav",
        75: "http://carolinegabriel.com/demo/js-keyboard/sounds/052.wav",
        79: "http://carolinegabriel.com/demo/js-keyboard/sounds/053.wav",
        76: "http://carolinegabriel.com/demo/js-keyboard/sounds/054.wav",
        80: "http://carolinegabriel.com/demo/js-keyboard/sounds/055.wav",
        186: "http://carolinegabriel.com/demo/js-keyboard/sounds/056.wav",
        "creepy" : "https://orangefreesounds.com/wp-content/uploads/2020/09/Creepy-piano-sound-effect.mp3?_=1"
    };
    let weSeeYouKeyCode = [];

    /**
     * Function to change color of all keys when hovering over them
     * @param whiteColor
     * @param blackColor
     * */
    const changeColor = (whiteColor, blackColor) => {
        for (let i = 0; i < white_key_notes.length; i++) {
            white_key_notes[i].style.color = whiteColor;
        }
        for (let i = 0; i < black_key_notes.length; i++) {
            black_key_notes[i].style.color = blackColor;
        }
    };

    /**
     * function to change the background of the key when pressed for both white and black keys
     * @param key
     */
    function keyPress(key){
        if (key === ';'){
            key = 'COLON';
        }
        let selector = "#" + key.toUpperCase();
        let note = document.querySelector(selector);
        if (!note) {
        console.error('No element found for selector:', selector);
        return; // Exit the function if no element is found
        }
        let color= note.classList[0];

        if(color === "white"){
           // Change the background color to gray
            note.style.backgroundColor = '#808080';

            // Change the background color back to white after a delay long enough to see color change but responsive to not linger
            setTimeout(() => {
                note.style.backgroundColor = '#ffffff';
            }, 300);
        }
        else{
            // Change the background color to gray
            note.style.backgroundColor = '#808080';

            // Change the background color back to white after a delay long enough to see color change but responsive to not linger
            setTimeout(() => {
                note.style.backgroundColor = '#111111';
            }, 300);
        }
        weSeeYou(key);
    }

   // Add event listeners to the piano
    piano.addEventListener("mouseover", function() {
        changeColor("black", "white"); // Change all white notes to black and black notes to white on mouseover
    });

    //detects in the mouse has left the piano
    piano.addEventListener("mouseout", function() {
        changeColor("white", "black"); // Revert colors on mouseout
    });

    function playSounds(keyCode) {
         // Check if the keyCode is in the sound object
        if (sound[keyCode]) {
            // Create a new Audio object with the corresponding sound URL
            let audio = new Audio(sound[keyCode]);
            // Play the sound
            audio.play();

            console.log(keyCode);
        }
    }
    //this function make sure piona play mp3, changes images, and disables piano
    function killPiano() {
        playSounds("creepy");
        var piano = document.getElementsByClassName('piano-background')[0];
        var content = document.getElementById('content-container');

        // Fade out piano and then fade in content
        piano.style.opacity = 0;
        piano.addEventListener('transitionend', function onFadeOut() {
            piano.removeEventListener('transitionend', onFadeOut); // Clean up the listener
            content.style.opacity = 1; // Fade in the content
        });
        dead = true;
    }

    //detects if sequence has been played weseeyou
    function weSeeYou(key) {
        const weSeeYouSequence = ['w', 'e', 's', 'e', 'e', 'y', 'o', 'u'];
        //  buffer to hold the last few characters typed
        if (typeof weSeeYouKeyCode === 'undefined') {
            weSeeYouKeyCode = [];
        }
        // append the new key pressed to the buffer
        weSeeYouKeyCode.push(key.toLocaleLowerCase());
        // limita the buffer to the last 8 characters
        if (weSeeYouKeyCode.length > weSeeYouSequence.length) {
            weSeeYouKeyCode.shift(); // Remove the oldest character
        }
        // checks if the current buffer matches the weSeeYouSequence
        if (weSeeYouKeyCode.length === weSeeYouSequence.length) {
            let match = true;
            for (let i = 0; i < weSeeYouSequence.length; i++) {
                if (weSeeYouKeyCode[i] !== weSeeYouSequence[i]) {
                    match = false;
                    break;
                }
            }
            if (match) {
                killPiano();
                console.log("Sequence detected: weSeeYou");
            }
        }
    }

    // key event listener to detect is a key is press also handles sounds of the keys
    document.addEventListener("keydown", function(event) {
       if(dead === false){
            keyPress(event.key); //change the background of all keys
            // Get the keyCode of the pressed key
            let keyCode = event.keyCode;
                playSounds(keyCode);
        }
    });
});