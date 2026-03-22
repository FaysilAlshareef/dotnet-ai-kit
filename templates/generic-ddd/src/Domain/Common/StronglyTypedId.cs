namespace {{ Company }}.{{ ProjectName }}.Domain.Common;

public abstract record StronglyTypedId(Guid Value)
{
    public override string ToString() => Value.ToString();
}
