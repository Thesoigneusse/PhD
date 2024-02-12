import torch
import Process_attention_weight as paw
import Concat_utils as cu

def process_concat_matrice(absolute_input_path: str):
    """Process une matrice de self-attention du mécanisme d'attention d'un modèle par concaténation

    Args:
        absolute_input_path (str): chemin absolue vers la matrice au format .json à lire

    Returns:
        dict: retourne un dictionnaire de la forme {"id": int,
                                                    "src": {
                                                        "matrices_attn_normalized_bpe" : [[k0 x k0, k0 x k1, ...],
                                                                                          [k1 x k0, k1 x k1, ...], ...]
                                                        "crt": [tokens de la phrase courante],
                                                        "ctx": [[tokens de la phrase k3], [tokens de la phrase k2] ...]
                                                    },
                                                    "tgt": {
                                                        "matrices_attn_normalized_bpe" : [[k0 x k0, k0 x k1, ...],
                                                                                          [k1 x k0, k1 x k1, ...], ...]
                                                        "crt": [tokens de la phrase courante],
                                                        "ctx": [[tokens de la phrase k3], [tokens de la phrase k2], ...]
                                                    }}
    """
    data= paw.lecture_data(absolute_input_path)

        ## SRC side ############################################################################################################################################################
    if type(data["src_tokens"]) == str:
        data["src_tokens"] = data["src_tokens"].split()

    # On corrige les éléments reçus
    data["src_tokens"] = cu.ajoute_eos_tokens_src(data["src_tokens"], \
                                                data["src_segments_labels"])

    # On découpe la phrase complete dans les différentes phrases présentes
    data["src_sentence"] = cu.full_sentence_to_ctx_and_crt(data["src_tokens"])
    src_contextes = len(data["src_sentence"])

    # On converti la matrice en torch.DoubleTensor
    data["enc_matrix"] = paw.convertion_matrice_str_to_float( data["enc_attn"])

    # On supprime les poids inférieur à une distribution uniforme
    data["enc_matrix_suppr_inf_unif"] = paw.suppression_inf_uniforme_tensor_src(data["enc_matrix"]) 

    # Découpage de la matrice de self-attention en matrices de phrase x phrase
    data["enc_matrices_attn"] = cu.cut_matrix_into_sentences(data["enc_matrix_suppr_inf_unif"], data["src_sentence"])

    # Normalisation de chaque matrice phrase x phrase
    data["enc_matrices_attn_normalized"] = []
    for i in range(src_contextes):
        temp = []
        for j in range(src_contextes):
            temp.append({"crt": data["enc_matrices_attn"][i][j]["crt"],
                "ctx": data["enc_matrices_attn"][i][j]["ctx"],
                "matrix": paw.normalise_tensor(data["enc_matrices_attn"][i][j]["matrix"])})
        data["enc_matrices_attn_normalized"].append(temp)

    # Fusion des BPEs pour chaque matrice phrase x phrase
    data["enc_matrices_attn_normalized_bpe"] = []
    for i in range(src_contextes):
        temp = []
        for j in range(src_contextes):
            temp.append({"crt": data["enc_matrices_attn_normalized"][i][j]["crt"],
                "ctx": data["enc_matrices_attn_normalized"][i][j]["ctx"],
                "matrix": paw.fusion_bpe(data["enc_matrices_attn_normalized"][i][j]["matrix"],
                                        data["enc_matrices_attn_normalized"][i][j]["crt"],
                                        data["enc_matrices_attn_normalized"][i][j]["ctx"])})
        data["enc_matrices_attn_normalized_bpe"].append(temp)



    ## TGT side ############################################################################################################################################################
    if type(data["tgt_tokens"]) == str:
        data["tgt_tokens"] = data["tgt_tokens"].split()

    # On corrige les éléments reçus
    data["tgt_tokens"] = cu.ajoute_eos_tokens_tgt(data["tgt_tokens"], \
                                                data["tgt_eos_pos"])

    # On découpe la phrase complete dans les différentes phrases présentes
    data["tgt_sentence"] = cu.full_sentence_to_ctx_and_crt(data["tgt_tokens"])
    tgt_contextes = len(data["tgt_sentence"])

    # On converti la matrice en torch.DoubleTensor
    data["dec_matrix"] = paw.convertion_matrice_str_to_float( data["dec_attn"])
    data["dec_matrix"] = torch.where(data["dec_matrix"] == -1e8, torch.tensor(0.0), data["dec_matrix"]) # replace value of -1e8 to 0.0

    # On supprime les poids inférieur à une distribution uniforme
    data["dec_matrix_suppr_inf_unif"] = paw.suppression_inf_uniforme_tensor_tgt(data["dec_matrix"].transpose(0,1))

    # Découpage de la matrice de self-attention en matrices de phrase x phrase
    data["dec_matrices_attn"] = cu.cut_matrix_into_sentences(data["dec_matrix_suppr_inf_unif"], data["tgt_sentence"])

    # Normalisation de chaque matrice phrase x phrase
    data["dec_matrices_attn_normalized"] = []
    for i in range(tgt_contextes):
        temp = []
        for j in range(tgt_contextes):
            temp.append({"crt": data["dec_matrices_attn"][i][j]["crt"],
                "ctx": data["dec_matrices_attn"][i][j]["ctx"],
                "matrix": paw.normalise_tensor(data["dec_matrices_attn"][i][j]["matrix"])})
        data["dec_matrices_attn_normalized"].append(temp)

    # Fusion des BPEs pour chaque matrice phrase x phrase
    data["dec_matrices_attn_normalized_bpe"] = []
    for i in range(tgt_contextes):
        temp = []
        for j in range(tgt_contextes):
            _matrice, _row_snt, _col_snt = paw.fusion_bpe(data["dec_matrices_attn_normalized"][i][j]["matrix"],
                                        data["dec_matrices_attn_normalized"][i][j]["crt"],
                                        data["dec_matrices_attn_normalized"][i][j]["ctx"])
            temp.append({"crt": _row_snt,
                "ctx": _col_snt,
                "matrix": _matrice})
        data["dec_matrices_attn_normalized_bpe"].append(temp)
    return {
        "id": data["id"],
        "src": {
            "matrices_attn_normalized_bpe": data["enc_matrices_attn_normalized_bpe"],
            "crt": data["src_sentence"][-1],
            "ctxs": data["src_sentence"][0:-1]
        },
        "tgt": {
            "matrices_attn_normalized_bpe": data["dec_matrices_attn_normalized_bpe"],
            "crt": data["tgt_sentence"][-1],
            "ctxs": data["tgt_sentence"][0:-1]
        }
    }

