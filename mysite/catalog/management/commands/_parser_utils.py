from decimal import Decimal, InvalidOperation


def emit(writer, level, message):
    writer(f"[{level}] {message}")


def emit_field(writer, field_name, raw_value, final_value, note=""):
    raw_repr = repr(raw_value)
    final_repr = repr(final_value)
    suffix = f" | {note}" if note else ""
    writer(f"    {field_name}: raw={raw_repr} -> final={final_repr}{suffix}")


def normalize_blank(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def parse_nullable_int(value):
    value = normalize_blank(value)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_nullable_decimal(value):
    value = normalize_blank(value)
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return None


def resolve_choice(model_class, field_name, raw_value, writer, aliases=None):
    raw_value = normalize_blank(raw_value)
    if raw_value is None:
        emit_field(writer, field_name, raw_value, None, "empty -> NULL")
        return None

    aliases = aliases or {}
    alias_map = {str(key).strip().casefold(): value for key, value in aliases.items()}
    candidate = alias_map.get(str(raw_value).strip().casefold(), raw_value)

    field = model_class._meta.get_field(field_name)
    value_map = {}
    label_map = {}
    for value, label in field.flatchoices:
        if value in ("", None):
            continue
        value_map[str(value).strip().casefold()] = value
        label_map[str(label).strip().casefold()] = value

    candidate_key = str(candidate).strip().casefold()
    resolved = value_map.get(candidate_key) or label_map.get(candidate_key)
    if resolved is None:
        emit_field(writer, field_name, raw_value, None, "not in model choices -> NULL")
        return None

    note = "matched alias" if candidate != raw_value else "matched choice"
    emit_field(writer, field_name, raw_value, resolved, note)
    return resolved


def normalize_model_payload(model_class, payload, writer, choice_aliases=None):
    normalized = {}
    choice_aliases = choice_aliases or {}

    for field_name, value in payload.items():
        field = model_class._meta.get_field(field_name)
        raw_value = value

        if field.choices:
            normalized[field_name] = resolve_choice(
                model_class,
                field_name,
                raw_value,
                writer,
                aliases=choice_aliases.get(field_name),
            )
            continue

        if field.get_internal_type() in {"CharField", "TextField"}:
            final_value = normalize_blank(raw_value)
            if final_value is None and getattr(field, "null", False):
                emit_field(writer, field_name, raw_value, None, "empty text -> NULL")
            else:
                emit_field(writer, field_name, raw_value, final_value)
            normalized[field_name] = final_value
            continue

        if field.get_internal_type() in {"PositiveIntegerField", "IntegerField"}:
            final_value = parse_nullable_int(raw_value)
            note = "invalid integer -> NULL" if raw_value not in (None, "") and final_value is None else ""
            emit_field(writer, field_name, raw_value, final_value, note)
            normalized[field_name] = final_value
            continue

        if field.get_internal_type() == "DecimalField":
            final_value = parse_nullable_decimal(raw_value)
            note = "invalid decimal -> NULL" if raw_value not in (None, "") and final_value is None else ""
            emit_field(writer, field_name, raw_value, final_value, note)
            normalized[field_name] = final_value
            continue

        emit_field(writer, field_name, raw_value, raw_value)
        normalized[field_name] = raw_value

    return normalized
