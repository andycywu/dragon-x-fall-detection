from pathlib import Path
import numpy as np
import flatbuffers
# 假設 tflite schema 產生的 python module 在同目錄 tflite/
from tflite.Model import Model
from tflite.TensorType import TensorType

def hook_fp16_to_fp32(tflite_in: str, tflite_out: str = None) -> str:
    """
    將 .tflite 檔中的所有 FLOAT16 tensor 上拋為 FLOAT32 並轉換其對應 buffer。
    回傳輸出檔路徑。若未找到任何 FLOAT16，直接複製輸入為輸出。
    """
    in_path = Path(tflite_in)
    out_path = Path(tflite_out) if tflite_out else in_path.with_suffix(".fp32.tflite")
    data = in_path.read_bytes()
    model = Model.GetRootAsModel(data, 0)
    fp16_tensor_ids = []
    affected_buffer_ids = set()
    for sg_idx in range(model.SubgraphsLength()):
        sg = model.Subgraphs(sg_idx)
        for t_idx in range(sg.TensorsLength()):
            t = sg.Tensors(t_idx)
            if t.Type() == TensorType.FLOAT16:
                fp16_tensor_ids.append((sg_idx, t_idx))
                buf_id = t.Buffer()
                affected_buffer_ids.add(buf_id)
    if not fp16_tensor_ids:
        out_path.write_bytes(data)
        return str(out_path)
    from tflite import Model as ModelTbl, Buffer as BufferTbl, Tensor as TensorTbl, SubGraph as SubGraphTbl, OperatorCode, Operator
    buffers = []
    for i in range(model.BuffersLength()):
        buf = model.Buffers(i)
        if buf.DataLength() > 0 and i in affected_buffer_ids:
            raw = bytes([buf.Data(j) for j in range(buf.DataLength())])
            arr_f16 = np.frombuffer(raw, dtype=np.float16)
            arr_f32 = arr_f16.astype(np.float32)
            new_raw = arr_f32.tobytes()
            buffers.append(new_raw)
        else:
            if buf.DataLength() > 0:
                raw = bytes([buf.Data(j) for j in range(buf.DataLength())])
                buffers.append(raw)
            else:
                buffers.append(b"")
    import flatbuffers
    builder = flatbuffers.Builder(2 * len(data))
    opcodes_off = []
    for i in range(model.OperatorCodesLength()):
        oc = model.OperatorCodes(i)
        from tflite.OperatorCode import OperatorCodeStart, OperatorCodeAddBuiltinCode, OperatorCodeAddVersion, OperatorCodeAddCustomCode, OperatorCodeEnd
        OperatorCodeStart(builder)
        OperatorCodeAddBuiltinCode(builder, oc.BuiltinCode())
        if oc.CustomCode():
            custom = oc.CustomCode().decode("utf-8")
            custom_off = builder.CreateString(custom)
            OperatorCodeAddCustomCode(builder, custom_off)
        OperatorCodeAddVersion(builder, oc.Version())
        opcodes_off.append(OperatorCodeEnd(builder))
    from tflite.Buffer import BufferStart, BufferAddData, BufferEnd
    bufs_off = []
    for raw in buffers:
        if raw:
            vec = builder.CreateByteVector(raw)
        else:
            vec = None
        BufferStart(builder)
        if vec is not None:
            BufferAddData(builder, vec)
        bufs_off.append(BufferEnd(builder))
    subgraphs_off = []
    for sg_idx in range(model.SubgraphsLength()):
        sg = model.Subgraphs(sg_idx)
        from tflite.Tensor import TensorStart, TensorAddShape, TensorAddType, TensorAddBuffer, TensorAddName, TensorAddQuantization, TensorEnd
        tensor_offs = []
        for t_idx in range(sg.TensorsLength()):
            t = sg.Tensors(t_idx)
            shape = [t.Shape(j) for j in range(t.ShapeLength())] if t.ShapeLength() > 0 else []
            if shape:
                shape_vec = builder.CreateNumpyVector(np.array(shape, dtype=np.int32))
            else:
                shape_vec = None
            name_off = builder.CreateString(t.Name().decode("utf-8")) if t.Name() else None
            quant_off = None
            if t.Quantization():
                q = t.Quantization()
                from tflite.QuantizationParameters import QuantizationParametersStart, QuantizationParametersEnd, QuantizationParametersAddScale, QuantizationParametersAddZeroPoint
                QuantizationParametersStart(builder)
                if q.ScaleLength() > 0:
                    scales = [q.Scale(i) for i in range(q.ScaleLength())]
                    scales_vec = builder.CreateNumpyVector(np.array(scales, dtype=np.float32))
                    QuantizationParametersAddScale(builder, scales_vec)
                if q.ZeroPointLength() > 0:
                    zps = [q.ZeroPoint(i) for i in range(q.ZeroPointLength())]
                    zps_vec = builder.CreateNumpyVector(np.array(zps, dtype=np.int64))
                    QuantizationParametersAddZeroPoint(builder, zps_vec)
                quant_off = QuantizationParametersEnd(builder)
            new_dtype = TensorType.FLOAT32 if t.Type() == TensorType.FLOAT16 else t.Type()
            TensorStart(builder)
            if shape_vec is not None:
                TensorAddShape(builder, shape_vec)
            TensorAddType(builder, new_dtype)
            TensorAddBuffer(builder, t.Buffer())
            if name_off is not None:
                TensorAddName(builder, name_off)
            if quant_off is not None:
                TensorAddQuantization(builder, quant_off)
            tensor_offs.append(TensorEnd(builder))
        def _build_int_vec(vals):
            if not vals:
                return None
            return builder.CreateNumpyVector(np.array(vals, dtype=np.int32))
        inputs = [sg.Inputs(i) for i in range(sg.InputsLength())]
        outputs = [sg.Outputs(i) for i in range(sg.OutputsLength())]
        from tflite.Operator import OperatorStart, OperatorEnd, OperatorAddInputs, OperatorAddOutputs, OperatorAddOpcodeIndex, OperatorAddBuiltinOptionsType, OperatorAddBuiltinOptions, OperatorAddCustomOptions
        op_offs = []
        for oi in range(sg.OperatorsLength()):
            op = sg.Operators(oi)
            OperatorStart(builder)
            OperatorAddOpcodeIndex(builder, op.OpcodeIndex())
            inps = [op.Inputs(i) for i in range(op.InputsLength())]
            outs = [op.Outputs(i) for i in range(op.OutputsLength())]
            vin = _build_int_vec(inps)
            vout = _build_int_vec(outs)
            if vin is not None:
                OperatorAddInputs(builder, vin)
            if vout is not None:
                OperatorAddOutputs(builder, vout)
            OperatorAddBuiltinOptionsType(builder, op.BuiltinOptionsType())
            if op.BuiltinOptionsAsNumpy() is not None:
                bo_vec = builder.CreateByteVector(bytes(op.BuiltinOptionsAsNumpy()))
                OperatorAddBuiltinOptions(builder, bo_vec)
            if op.CustomOptionsLength() > 0:
                co_vec = builder.CreateByteVector(bytes([op.CustomOptions(i) for i in range(op.CustomOptionsLength())]))
                OperatorAddCustomOptions(builder, co_vec)
            op_offs.append(OperatorEnd(builder))
        def _build_vec(objs):
            if not objs:
                return None
            builder.StartVector(4, len(objs), 4)
            for off in reversed(objs):
                builder.PrependUOffsetTRelative(off)
            return builder.EndVector()
        tensors_vec = _build_vec(tensor_offs)
        ops_vec = _build_vec(op_offs)
        inputs_vec = _build_int_vec(inputs)
        outputs_vec = _build_int_vec(outputs)
        from tflite.SubGraph import SubGraphStart, SubGraphAddTensors, SubGraphAddInputs, SubGraphAddOutputs, SubGraphAddOperators, SubGraphAddName, SubGraphEnd
        SubGraphStart(builder)
        if tensors_vec: SubGraphAddTensors(builder, tensors_vec)
        if inputs_vec is not None: SubGraphAddInputs(builder, inputs_vec)
        if outputs_vec is not None: SubGraphAddOutputs(builder, outputs_vec)
        if ops_vec: SubGraphAddOperators(builder, ops_vec)
        if sg.Name():
            SubGraphAddName(builder, builder.CreateString(sg.Name().decode("utf-8")))
        subgraphs_off.append(SubGraphEnd(builder))
    def _build_vec_uoffset(items):
        if not items:
            return None
        builder.StartVector(4, len(items), 4)
        for off in reversed(items):
            builder.PrependUOffsetTRelative(off)
        return builder.EndVector()
    opcodes_vec = _build_vec_uoffset(opcodes_off)
    subgraphs_vec = _build_vec_uoffset(subgraphs_off)
    buffers_vec = _build_vec_uoffset(bufs_off)
    from tflite.Model import ModelStart, ModelAddVersion, ModelAddOperatorCodes, ModelAddSubgraphs, ModelAddBuffers, ModelEnd
    ModelStart(builder)
    ModelAddVersion(builder, model.Version())
    if opcodes_vec: ModelAddOperatorCodes(builder, opcodes_vec)
    if subgraphs_vec: ModelAddSubgraphs(builder, subgraphs_vec)
    if buffers_vec: ModelAddBuffers(builder, buffers_vec)
    root = ModelEnd(builder)
    builder.Finish(root)
    out_path.write_bytes(builder.Output())
    return str(out_path)
