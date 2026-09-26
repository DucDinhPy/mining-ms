using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using MineOps.Api.Models;

namespace MineOps.Api.Data.Configurations;

public class CameraConfiguration
    : IEntityTypeConfiguration<Camera>
{
    public void Configure(
        EntityTypeBuilder<Camera> entity)
    {
        entity.ToTable("cameras");

        entity.HasKey(x => x.Id);

        entity.Property(x => x.Name)
            .HasMaxLength(150)
            .IsRequired();

        entity.Property(x => x.StreamUrl)
            .HasMaxLength(2000)
            .IsRequired();

        entity.Property(x => x.Status)
            .HasConversion<string>()
            .HasMaxLength(30)
            .IsRequired();

        entity.Property(x => x.Location)
            .HasMaxLength(250)
            .IsRequired();

        entity.Property(x => x.Description)
            .HasMaxLength(1000);

        entity.HasIndex(x => x.Name);
        entity.HasIndex(x => x.Status);
    }
}