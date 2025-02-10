import sys
import torch
# from fairseq import fairseq
from fairseq.fairseq import checkpoint_utils
import soundfile
import torch.nn.functional as F
import torchaudio.sox_effects as ta_sox

import torchaudio
torchaudio.set_audio_backend("ffmpeg")
print(f"-----------------{torchaudio.get_audio_backend()}")

model_path = sys.argv[1]
audio_path = sys.argv[2]

device_type = None

if torch.cuda.is_available():
	print(f"-----cuda found")
	device = torch.device("cuda")
# elif torch.backends.mps.is_available():
# 	print(f"-----metal found")
# 	device = torch.device("mps")
else:
	device = torch.device("cpu")

audio, rate = soundfile.read(audio_path, dtype="float32")
effects = [["gain", "-n"]]
input_sample, rate = ta_sox.apply_effects_tensor(torch.tensor(audio).unsqueeze(0), rate, effects)

input_sample = input_sample.float().to(device)

with torch.no_grad():
	input_sample = F.layer_norm(input_sample, input_sample.shape)

model, cfg, task = checkpoint_utils.load_model_ensemble_and_task([model_path])

print(type(cfg))
print(cfg)

model = model[0]
model.to(device)
model.eval()

token = task.target_dictionary
logits = model(source=input_sample, padding_mask=None)["encoder_out"]
predicted_ids = torch.argmax(logits[:, 0], axis=-1)
predicted_ids = torch.unique_consecutive(predicted_ids).tolist()
transcription = token.string(predicted_ids)
transcription = transcription.replace(' ','').replace('|',' ').strip()
print(transcription)
