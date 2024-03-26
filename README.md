What is this?

I aimed to create a simple way for my kids to interact with 'the robot on dad's phone.' However after making it, I found I really enjoyed having one on my desk as well.

After exploring various options and contemplating building something from the ground up, I discovered the Google AIY Voice Kit, released in 2017. As of 2024, it appears that the best version of this kit for my needs is V1, which includes the 'Voice Hat' instead of the 'Voice Bonnet.'

The objective is to develop a voice assistant that has a pleasant voice, an easy-to-use interface, and is highly intelligent.

Requirements:

    Google AIY Voice Kit V1
    Raspberry Pi 3 or Raspberry Pi Zero W (other models might also work, but are not tested)
    MicroSD Card (8GB or larger)
    Micro USB cable
    USB Power Supply (must be reliable, as Raspberry Pis are sensitive to power quality)
    An OpenAI API Key
    Another computer to SSH into the Pi

Install process:
1) Use the Raspberry Pi Imager to pick up the lite bullseye image and flash it to your microsdcard. Make sure you add your wifi information, create a user, set a password, and enable ssh
2) Pick a software to connect to the Raspberry PI, I like VsCode but you can use putty too
3) SSH into you Pi and run some commands
