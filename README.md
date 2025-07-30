## This is my current project! ##
I'm a big EDM fan, and I thought it would be cool to make a DMX laser controller with python. The goal is to implement a neural network that makes laser shows.

## Current Progress ## 
I've spent some time making patterns with dmx signals and a tkinter labeling tool. I've began labeling songs with pattern groups, and I hope to begin working on the neural net soon.
One NN will classify speed at each frame of a song, and another will classify patterns. The combination of the two will hopefully result in a cool laser show.

I also am continously developing new patterns and modifying old ones. Even if the Neural Net works great and labels songs perfectly, the shows will only be as good as the patterns I develop.

**You'll notice a lot of magic numbers. DMX signals take in hardware-specific values in a 0-255 range for hardware-specific channels.** 
I've labeled a good portion of the dmx.set_channel calls in *some* files, but I'm not going to label everything in each file - If you're really curious as to what they're doing, you can check out the manual of the laser that im using, posted in the root dir.

