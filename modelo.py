"""Inferencia NumPy de pesos propios. No pickle, servicios web ni credenciales."""
import numpy as np


def logsumexp(x, axis=None):
    x = np.asarray(x)
    maximum = np.max(x, axis=axis, keepdims=True)
    result = maximum + np.log(np.exp(x - maximum).sum(axis=axis, keepdims=True))
    return result.squeeze() if axis is None else result.squeeze(axis)


def inferir(X, weights, prefix, bound):
    """X debe estar estandarizada y acotada como el entrenamiento correspondiente."""
    h = np.asarray(X, dtype=np.float32)
    for j in (0, 3):
        h = h @ weights[prefix + f'__w{j}'].T + weights[prefix + f'__b{j}']
        e = np.exp(-np.abs(h))
        h = h * np.where(h >= 0, 1 / (1 + e), e / (1 + e))  # SiLU estable.
    g = (h @ weights[prefix + '__w6'].T + weights[prefix + '__b6']).reshape(-1)
    anchor = (X * weights[prefix + '__anchor']).sum(-1)
    return anchor + bound * np.tanh(g), anchor


def miembros_decil(values, background, fraction=0.1):
    """Asigna empates fraccionalmente, manteniendo el presupuesto de área."""
    threshold = float(np.quantile(background, 1 - fraction))
    greater = np.mean(background > threshold)
    tied = np.mean(background == threshold)
    tie_weight = np.clip((fraction - greater) / tied, 0, 1) if tied > 0 else 0.0
    return (values > threshold).astype(float) + (values == threshold) * tie_weight


def evaluar(fe, fb, valid):
    if not np.all(valid.sum(1) > 0):
        raise ValueError('Reporte sin soporte válido')
    norm = logsumexp(fb) - np.log(len(fb))
    event = logsumexp(np.where(valid, fe, -np.inf), axis=1) - np.log(valid.sum(1)) - norm
    capture = (miembros_decil(fe, fb) * valid).sum(1) / valid.sum(1)
    return event, capture


def ensamble(fes, fbs):
    """Promedio de densidades normalizadas, no promedio de log-scores."""
    norms = [logsumexp(b) - np.log(len(b)) for b in fbs]
    fe = logsumexp(np.stack([e - n for e, n in zip(fes, norms)]), axis=0) - np.log(len(fes))
    fb = logsumexp(np.stack([b - n for b, n in zip(fbs, norms)]), axis=0) - np.log(len(fbs))
    return fe, fb
