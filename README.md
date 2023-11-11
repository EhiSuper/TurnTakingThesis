# TurnTakingThesis
This is the repository about my Thesis in Turn Taking regarding Human robot interaction

In this project there is an implementation of a real time remote voice activity detection application. The application also manages the state of the conversation thanks to a set of states.
For the real time communication part we used the WebRTC technology while for the VAD part we used the Silero VAD model available with PyTorch. 
The application has also a websocket component able to send the current status of the conversation to external modules. The module has been developed with the aim to be inserted inside the Abel software architecture. For more informations please check the documentation prensent in the Thesis pdf.

Installation:
To install all the requirements for the application please run: " pip install -r requirements.txt "

