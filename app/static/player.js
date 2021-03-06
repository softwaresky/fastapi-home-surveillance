class Player {
    constructor(config, socket) {
        let self = this;
        this.config = config;
        this.socket = socket;
        this.audioCtx = null;
        this.silence = new Float32Array(this.config.bufferSize);
        this.playing = false;

        this.audioQueue = {
            buffer: new Float32Array(0),

            write: function (chunk) {
                let currentLength = this.buffer.length;
                let newBuffer = new Float32Array(currentLength + chunk.length);
                newBuffer.set(this.buffer, 0);
                newBuffer.set(chunk, currentLength);
                this.buffer = newBuffer;
            },

            read: function (nSamples) {
                let samplesToPlay = this.buffer.subarray(0, nSamples);
                this.buffer = this.buffer.subarray(nSamples, this.buffer.length);
                return samplesToPlay;
            },

            length: function () {
                return this.buffer.length;
            },

            clear: function () {
                this.buffer = new Float32Array(0)
            }
        }

        socket.onmessage = function (event) {

            if (self.scriptNode) {
                // console.log(event);
                // const list = JSON.parse(event.data);

                // const bytes = Uint8Array.from(event.data, c => c.charCodeAt(0));
                // const floats = new Float32Array(bytes.buffer);
                // console.log(floats);

                // let array = new Float32Array(list);
                // self.audioQueue.write(array);


                // let testDataInt = new Uint8Array(event.data);
                // console.log(testDataInt);
                // const array = self.int16ToFloat32(bytes, 0, event.data.length);
                // console.log(array);

                // const uint8View = new Uint8Array(event.data);
                // const floats = new Float32Array(uint8View.buffer);

                // self.audioQueue.write(floats);

                let reader = new FileReader();
                reader.onload = function () {
                    const floats = new Float32Array(reader.result);
                    self.audioQueue.write(floats);
                };
                reader.readAsArrayBuffer(event.data)

            }
        };

        // socket.on('sound', function (data) {
        //     if (self.scriptNode) {
        //         //console.log("received");
        //         let array = new Float32Array(data.chunk);
        //         console.log(array);
        //         self.audioQueue.write(array);
        //
        //         /*console.log(data.chunk);
        //         var testDataInt = new Uint8Array(data.chunk);
        //         console.log(testDataInt);
        //         let array = self.int16ToFloat32(testDataInt, 0, data.chunk.length);
        //         console.log(array);
        //         self.audioQueue.write(array);*/
        //     }
        // });
    }

    play() {
        this.playing = true;
        this.audioCtx = new AudioContext();
        this.scriptNode = this.audioCtx.createScriptProcessor(this.config.bufferSize, 1, 1);
        this.scriptNode.onaudioprocess = (e) => {
            if (this.audioQueue.length()) {
                e.outputBuffer.getChannelData(0).set(this.audioQueue.read(this.config.bufferSize));
            } else {
                e.outputBuffer.getChannelData(0).set(this.silence);
            }
        }

        this.scriptNode.connect(this.audioCtx.destination);
    }

    stop() {
        this.audioQueue.clear();
        this.scriptNode.disconnect();
        this.scriptNode = null;
    }

    isPlaying() {
        return !!this.scriptNode;
    }

    int16ToFloat32(inputArray, startIndex, length) {
        let output = new Float32Array(inputArray.length - startIndex);
        for (let i = startIndex; i < length; i++) {
            let int = inputArray[i];
            // If the high bit is on, then it is a negative number, and actually counts backwards.
            output[i] = (int >= 0x8000) ? -(0x10000 - int) / 0x8000 : int / 0x7FFF;
        }
        return output;
    }
}
