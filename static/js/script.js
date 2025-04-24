// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Navigation menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
    }
    
    // Accordion for FAQ section
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    if (accordionHeaders) {
        accordionHeaders.forEach(header => {
            header.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                
                if (content.classList.contains('active')) {
                    content.classList.remove('active');
                } else {
                    content.classList.add('active');
                }
            });
        });
    }
    
    // Chat functionality
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Mode toggle switch
    const modeToggle = document.getElementById('mode-toggle');
    const toggleStatus = document.getElementById('toggle-status');
    const uploadSection = document.getElementById('upload-section');
    
    if (modeToggle && toggleStatus && uploadSection) {
        modeToggle.addEventListener('change', function() {
            const isChecked = this.checked;
            toggleStatus.textContent = isChecked ? 'ON' : 'OFF';
            
            if (isChecked) {
                uploadSection.style.display = 'block';
            } else {
                uploadSection.style.display = 'none';
            }
            
            // Send the toggle state to the server
            fetch('/switch_toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_mode: isChecked
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Error toggling mode');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    // File upload functionality
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const filesList = document.getElementById('files-list');
    
    if (uploadForm && fileInput && uploadStatus) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const file = fileInput.files[0];
            if (!file) {
                uploadStatus.textContent = 'No file selected';
                uploadStatus.style.color = 'var(--error-color)';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            uploadStatus.textContent = 'Uploading...';
            uploadStatus.style.color = 'var(--text-secondary)';
            
            fetch('/upload', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.textContent = 'File uploaded successfully!';
                    uploadStatus.style.color = 'var(--success-color)';
                    fileInput.value = '';
                    
                    // Add the file to the files list
                    if (filesList) {
                        const li = document.createElement('li');
                        li.textContent = data.filename;
                        filesList.appendChild(li);
                    }
                } else {
                    uploadStatus.textContent = data.error || 'Upload failed';
                    uploadStatus.style.color = 'var(--error-color)';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                uploadStatus.textContent = 'Upload failed';
                uploadStatus.style.color = 'var(--error-color)';
            });
        });
    }
    
    // Chat form submission
    if (chatForm && userInput && chatMessages) {
        // Load chat history on page load
        fetch('/history')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.history && data.history.length > 0) {
                    chatMessages.innerHTML = ''; // Clear default message
                    
                    data.history.forEach(message => {
                        appendMessage(message.role === 'user', message.content);
                    });
                    
                    // Scroll to bottom of chat
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error fetching history:', error);
            });
        
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const question = userInput.value.trim();
            if (!question) return;
            
            // Add user message to chat
            appendMessage(true, question);
            
            // Clear input
            userInput.value = '';
            
            // Show typing indicator
            typingIndicator.style.display = 'flex';
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Send question to server
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question
                }),
            })
            .then(response => response.json())
            .then(data => {
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                if (data.success) {
                    // Add bot message to chat
                    appendMessage(false, data.answer);
                } else {
                    // Add error message
                    appendMessage(false, 'Sorry, I encountered an error: ' + (data.error || 'Unknown error'));
                }
                
                // Scroll to bottom of chat
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                // Add error message
                appendMessage(false, 'Sorry, there was a network error. Please try again.');
                
                console.error('Error:', error);
                
                // Scroll to bottom of chat
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        });
    }
    
    // Contact form submission
    const contactForm = document.querySelector('.contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // In a real application, you would submit this to a server
            alert('Thank you for your message! This is a demo, so your message was not actually sent.');
            contactForm.reset();
        });
    }
    
    // Function to append a message to the chat
    function appendMessage(isUser, content) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Handle multi-line messages
        content.split('\n').forEach(line => {
            if (line.trim() !== '') {
                const paragraph = document.createElement('p');
                paragraph.textContent = line;
                messageContent.appendChild(paragraph);
            }
        });
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = 'Just now';
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        chatMessages.appendChild(messageDiv);
    }
});