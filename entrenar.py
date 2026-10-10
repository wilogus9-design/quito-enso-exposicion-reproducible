"""Reentrena seis redes propias por combinación, usando anclas y splits congelados.

PyTorch es opcional. La ejecución estándar de reproducir.py sólo exige NumPy.
No se modifica PESOS.npz, las referencias ni la selección publicada.
"""
from pathlib import Path
import json
import math
import numpy as np


def train(key, device, output):
    import torch
    from torch import nn
    root = Path(__file__).resolve().parent
    states = json.loads((root / 'PARAMETROS.json').read_text(encoding='utf-8'))
    if key not in states:
        raise ValueError('Combinación desconocida: ' + key)
    output.mkdir(parents=True, exist_ok=True)
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA solicitado pero no disponible')
    torch.set_num_threads(4)
    with np.load(root / f'DATOS_{key}.npz', allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}

    class ResidualNet(nn.Module):
        def __init__(self, anchor, bound):
            super().__init__()
            self.register_buffer('anchor', torch.as_tensor(anchor, dtype=torch.float32))
            self.bound = bound
            self.layers = nn.Sequential(nn.Linear(len(anchor), 16), nn.SiLU(), nn.Dropout(.10),
                                        nn.Linear(16, 8), nn.SiLU(), nn.Dropout(.10), nn.Linear(8, 1))
            nn.init.zeros_(self.layers[-1].weight)
            nn.init.zeros_(self.layers[-1].bias)

        def residual(self, x):
            return self.bound * torch.tanh(self.layers(x).squeeze(-1))

        def forward(self, x):
            return (x * self.anchor).sum(-1) + self.residual(x)

    Xb = torch.as_tensor(d['Xb'], device=device)
    Xe = torch.as_tensor(d['Xe'], device=device)
    valid = torch.as_tensor(d['valid_e'], device=device)
    et, ec = Xe[d['etrain']], Xe[d['ecal']]
    vt, vc = valid[d['etrain']], valid[d['ecal']]
    bt, bc = Xb[d['btrain']], Xb[d['bcal']]
    audit, results, tensors = [], [], {}
    for bound in (0.25, 1.0):
        scores = []
        for seed in (5101, 5102, 5103):
            torch.manual_seed(seed)
            rng = np.random.default_rng(seed)
            model = ResidualNet(d['anchor'], bound).to(device)
            optimizer = torch.optim.AdamW(model.layers.parameters(), lr=.002, weight_decay=.05)
            best, best_state, best_epoch = -float('inf'), None, None
            for epoch in range(301):
                model.train()
                idx = torch.as_tensor(rng.choice(len(bt), min(16384, len(bt)), replace=False), device=device)
                fe = model(et).masked_fill(~vt, -torch.inf)
                ev = torch.logsumexp(fe, 1) - torch.log(vt.sum(1))
                fb, residual = model(bt[idx]), model.residual(bt[idx])
                loss = torch.logsumexp(fb, 0) - math.log(len(fb)) - ev.mean() + .10 * (residual ** 2).mean()
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
                optimizer.step()
                if epoch % 10 == 0:
                    model.eval()
                    with torch.no_grad():
                        ce = model(ec).masked_fill(~vc, -torch.inf)
                        score = float((torch.logsumexp(ce, 1) - torch.log(vc.sum(1))).mean()
                                      - torch.logsumexp(model(bc), 0) + math.log(len(bc)))
                    if score > best:
                        best, best_epoch = score, epoch
                        best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            prefix = key + '__B' + str(bound).replace('.', 'p') + '__s' + str(seed)
            tensors[prefix + '__anchor'] = best_state['anchor'].numpy()
            for j in (0, 3, 6):
                tensors[prefix + f'__w{j}'] = best_state[f'layers.{j}.weight'].numpy()
                tensors[prefix + f'__b{j}'] = best_state[f'layers.{j}.bias'].numpy()
            scores.append(best)
            audit.append(dict(key=key, bound=bound, seed=seed, epoch=best_epoch,
                              cal_log_density=best, torch_version=torch.__version__, device=device))
            print('Entrenado:', prefix, 'epoch', best_epoch, 'cal', best, flush=True)
        results.append([float(np.mean(scores)), bound])
    np.savez_compressed(output / 'PESOS_REENTRENADOS.npz', **tensors)
    report = dict(models=audit, bound_selected_by_calibration=max(results)[1],
                  test_used_for_selection=False, frozen_anchor=True,
                  note='Diferencias CPU/CUDA/versiones pueden impedir igualdad bit a bit')
    (output / 'ENTRENAMIENTO.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
