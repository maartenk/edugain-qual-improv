"""
Output formatting module for eduGAIN analysis results.

Provides various formatters for analysis results including:
- Summary statistics for terminal output
- Detailed markdown reports
- CSV exports for entities and federations
"""

import csv
import sys


def print_summary(stats: dict) -> None:
    """Print summary statistics with positive framing."""
    total = stats["total_entities"]
    total_sps = stats["total_sps"]
    total_idps = stats["total_idps"]

    if total == 0:
        print("No entities found in metadata.", file=sys.stderr)
        return

    print(
        "\n=== eduGAIN Quality Analysis: Privacy, Security & SIRTFI Coverage ===",
        file=sys.stderr,
    )
    print(
        f"Total entities analyzed: {total:,} (SPs: {total_sps:,}, IdPs: {total_idps:,})",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    # Privacy statement statistics - SP only
    if total_sps > 0:
        sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
        sp_missing_privacy_pct = (stats["sps_missing_privacy"] / total_sps) * 100
        print("📊 Privacy Statement URL Coverage (SPs only):", file=sys.stderr)
        print(
            f"  ✅ SPs with privacy statements: {stats['sps_has_privacy']:,} out of {total_sps:,} ({sp_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing privacy statements: {stats['sps_missing_privacy']:,} out of {total_sps:,} ({sp_missing_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Security contact statistics - tree format
    total_security_pct = (stats["total_has_security"] / total) * 100

    # Color emoji based on percentage
    if total_security_pct >= 80:
        total_security_emoji = "🟢"
    elif total_security_pct >= 50:
        total_security_emoji = "🟡"
    else:
        total_security_emoji = "🔴"

    print(
        f"🔒 Security Contact Coverage: {total_security_emoji} {stats['total_has_security']:,}/{total:,} ({total_security_pct:.1f}%)",
        file=sys.stderr,
    )

    # Split security stats by entity type with tree structure
    if total_sps > 0:
        sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
        sp_security_emoji = (
            "🟢" if sp_security_pct >= 80 else "🟡" if sp_security_pct >= 50 else "🔴"
        )
        print(
            f"  ├─ SPs: {sp_security_emoji} {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%)",
            file=sys.stderr,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        idp_security_emoji = (
            "🟢" if idp_security_pct >= 80 else "🟡" if idp_security_pct >= 50 else "🔴"
        )
        print(
            f"  └─ IdPs: {idp_security_emoji} {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # SIRTFI certification statistics - tree format
    total_sirtfi_pct = (stats["total_has_sirtfi"] / total) * 100

    # Color emoji based on percentage
    if total_sirtfi_pct >= 80:
        total_sirtfi_emoji = "🟢"
    elif total_sirtfi_pct >= 50:
        total_sirtfi_emoji = "🟡"
    else:
        total_sirtfi_emoji = "🔴"

    print(
        f"🔰 SIRTFI Certification Coverage: {total_sirtfi_emoji} {stats['total_has_sirtfi']:,}/{total:,} ({total_sirtfi_pct:.1f}%)",
        file=sys.stderr,
    )

    # Split SIRTFI stats by entity type with tree structure
    if total_sps > 0:
        sp_sirtfi_pct = (stats["sps_has_sirtfi"] / total_sps) * 100
        sp_sirtfi_emoji = (
            "🟢" if sp_sirtfi_pct >= 80 else "🟡" if sp_sirtfi_pct >= 50 else "🔴"
        )
        print(
            f"  ├─ SPs: {sp_sirtfi_emoji} {stats['sps_has_sirtfi']:,}/{total_sps:,} ({sp_sirtfi_pct:.1f}%)",
            file=sys.stderr,
        )

    if total_idps > 0:
        idp_sirtfi_pct = (stats["idps_has_sirtfi"] / total_idps) * 100
        idp_sirtfi_emoji = (
            "🟢" if idp_sirtfi_pct >= 80 else "🟡" if idp_sirtfi_pct >= 50 else "🔴"
        )
        print(
            f"  └─ IdPs: {idp_sirtfi_emoji} {stats['idps_has_sirtfi']:,}/{total_idps:,} ({idp_sirtfi_pct:.1f}%)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # Combined statistics - SP only (since privacy is SP-only)
    if total_sps > 0:
        sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
        sp_missing_both_pct = (stats["sps_missing_both"] / total_sps) * 100
        sp_has_at_least_one = total_sps - stats["sps_missing_both"]
        sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100

        print("📈 Combined Coverage Summary (SPs only):", file=sys.stderr)
        print(
            f"  🌟 SPs with BOTH privacy & security: {stats['sps_has_both']:,} out of {total_sps:,} ({sp_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ⚡ SPs with AT LEAST ONE (privacy or security): {sp_has_at_least_one:,} out of {total_sps:,} ({sp_at_least_one_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing BOTH privacy & security: {stats['sps_missing_both']:,} out of {total_sps:,} ({sp_missing_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Key insights for both entity types
    print("💡 Key Insights:", file=sys.stderr)

    # SP insights
    if total_sps > 0:
        print(
            f"  • {sp_at_least_one_pct:.1f}% of SPs provide at least basic compliance",
            file=sys.stderr,
        )
        print(
            f"  • {sp_both_pct:.1f}% of SPs achieve full compliance (security contact + privacy statement)",
            file=sys.stderr,
        )

    # IdP insights
    if total_idps > 0:
        print(
            f"  • {idp_security_pct:.1f}% of IdPs have security contacts (IdPs don't use privacy statements)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # Privacy URL Accessibility Check (if enabled)
    if stats.get("validation_enabled", False):
        urls_checked = stats["urls_checked"]
        if urls_checked > 0:
            print("🔗 Privacy Statement URL Check:", file=sys.stderr)
            print(
                f"  📊 Checked {urls_checked:,} privacy statement links",
                file=sys.stderr,
            )
            print("", file=sys.stderr)

            # Simple accessibility summary
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100
            broken_pct = (stats["urls_broken"] / urls_checked) * 100

            print(
                f"  ✅ {stats['urls_accessible']:,} links working ({accessibility_pct:.1f}%)",
                file=sys.stderr,
            )
            print(
                f"  ❌ {stats['urls_broken']:,} links broken ({broken_pct:.1f}%)",
                file=sys.stderr,
            )
            print("", file=sys.stderr)

    print(
        "💡 For detailed entity lists, federation reports, or CSV exports, use --help to see all options.",
        file=sys.stderr,
    )


def print_summary_markdown(stats: dict, output_file=sys.stderr) -> None:
    """Print main summary statistics in markdown format."""
    total = stats["total_entities"]
    total_sps = stats["total_sps"]
    total_idps = stats["total_idps"]

    if total == 0:
        print("# 📊 eduGAIN Quality Analysis Report", file=output_file)
        print("", file=output_file)
        print("**No entities found in the metadata.**", file=output_file)
        return

    print("# 📊 eduGAIN Quality Analysis Report", file=output_file)
    print("", file=output_file)
    print(
        f"**Analysis Summary:** {total:,} entities ({total_sps:,} SPs, {total_idps:,} IdPs) from eduGAIN metadata",
        file=output_file,
    )
    print("", file=output_file)

    # Privacy statistics - SP only
    if total_sps > 0:
        sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
        sp_missing_privacy_pct = (stats["sps_missing_privacy"] / total_sps) * 100

        privacy_status = (
            "🟢" if sp_privacy_pct >= 80 else "🟡" if sp_privacy_pct >= 50 else "🔴"
        )

        print("## 📊 Privacy Statement Coverage", file=output_file)
        print(
            "*Service Providers only (IdPs typically don't publish privacy statements)*",
            file=output_file,
        )
        print("", file=output_file)
        print(
            f"- **{privacy_status} SPs with Privacy Statements:** {stats['sps_has_privacy']:,}/{total_sps:,} ({sp_privacy_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **❌ SPs Missing Privacy Statements:** {stats['sps_missing_privacy']:,}/{total_sps:,} ({sp_missing_privacy_pct:.1f}%)",
            file=output_file,
        )
        print("", file=output_file)

    # Security contact statistics - both entity types
    total_security_pct = (stats["total_has_security"] / total) * 100
    total_missing_security_pct = (stats["total_missing_security"] / total) * 100

    security_status = (
        "🟢" if total_security_pct >= 80 else "🟡" if total_security_pct >= 50 else "🔴"
    )

    print("## 🔒 Security Contact Coverage", file=output_file)
    print("*Both Service Providers and Identity Providers*", file=output_file)
    print("", file=output_file)
    print(
        f"- **{security_status} Total with Security Contacts:** {stats['total_has_security']:,}/{total:,} ({total_security_pct:.1f}%)",
        file=output_file,
    )
    print(
        f"- **❌ Total Missing Security Contacts:** {stats['total_missing_security']:,}/{total:,} ({total_missing_security_pct:.1f}%)",
        file=output_file,
    )

    # Entity type breakdown
    if total_sps > 0:
        sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
        sp_security_status = (
            "🟢" if sp_security_pct >= 80 else "🟡" if sp_security_pct >= 50 else "🔴"
        )
        print(
            f"  - **{sp_security_status} Service Providers:** {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%)",
            file=output_file,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        idp_security_status = (
            "🟢" if idp_security_pct >= 80 else "🟡" if idp_security_pct >= 50 else "🔴"
        )
        print(
            f"  - **{idp_security_status} Identity Providers:** {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
            file=output_file,
        )

    print("", file=output_file)

    # SIRTFI certification statistics - both entity types
    total_sirtfi_pct = (stats["total_has_sirtfi"] / total) * 100
    total_missing_sirtfi_pct = (stats["total_missing_sirtfi"] / total) * 100

    sirtfi_status = (
        "🟢" if total_sirtfi_pct >= 80 else "🟡" if total_sirtfi_pct >= 50 else "🔴"
    )

    print("## 🔰 SIRTFI Certification Coverage", file=output_file)
    print(
        "*Security Incident Response Trust Framework for Federated Identity*",
        file=output_file,
    )
    print("", file=output_file)
    print(
        f"- **{sirtfi_status} Total with SIRTFI:** {stats['total_has_sirtfi']:,}/{total:,} ({total_sirtfi_pct:.1f}%)",
        file=output_file,
    )
    print(
        f"- **❌ Total without SIRTFI:** {stats['total_missing_sirtfi']:,}/{total:,} ({total_missing_sirtfi_pct:.1f}%)",
        file=output_file,
    )

    # Entity type breakdown
    if total_sps > 0:
        sp_sirtfi_pct = (stats["sps_has_sirtfi"] / total_sps) * 100
        sp_sirtfi_status = (
            "🟢" if sp_sirtfi_pct >= 80 else "🟡" if sp_sirtfi_pct >= 50 else "🔴"
        )
        print(
            f"  - **{sp_sirtfi_status} Service Providers:** {stats['sps_has_sirtfi']:,}/{total_sps:,} ({sp_sirtfi_pct:.1f}%)",
            file=output_file,
        )

    if total_idps > 0:
        idp_sirtfi_pct = (stats["idps_has_sirtfi"] / total_idps) * 100
        idp_sirtfi_status = (
            "🟢" if idp_sirtfi_pct >= 80 else "🟡" if idp_sirtfi_pct >= 50 else "🔴"
        )
        print(
            f"  - **{idp_sirtfi_status} Identity Providers:** {stats['idps_has_sirtfi']:,}/{total_idps:,} ({idp_sirtfi_pct:.1f}%)",
            file=output_file,
        )

    print("", file=output_file)

    # Combined compliance summary for SPs
    if total_sps > 0:
        sp_missing_both = stats["sps_missing_both"]
        sp_has_at_least_one = total_sps - sp_missing_both

        sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
        sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100
        sp_missing_both_pct = (sp_missing_both / total_sps) * 100

        compliance_status = (
            "🟢" if sp_both_pct >= 80 else "🟡" if sp_both_pct >= 50 else "🔴"
        )

        print("## 📈 SP Compliance Summary", file=output_file)
        print(
            "*Combined privacy statement and security contact compliance for Service Providers*",
            file=output_file,
        )
        print("", file=output_file)
        print(
            f"- **{compliance_status} Full Compliance (Both):** {stats['sps_has_both']:,}/{total_sps:,} ({sp_both_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **⚡ Partial Compliance (At Least One):** {sp_has_at_least_one:,}/{total_sps:,} ({sp_at_least_one_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **❌ No Compliance (Missing Both):** {sp_missing_both:,}/{total_sps:,} ({sp_missing_both_pct:.1f}%)",
            file=output_file,
        )
        print("", file=output_file)

    # Key Insights
    print("## 💡 Key Insights", file=output_file)

    if total_sps > 0:
        print(
            f"- {sp_at_least_one_pct:.1f}% of SPs provide at least basic compliance",
            file=output_file,
        )
        print(
            f"- {sp_both_pct:.1f}% of SPs achieve full compliance with both requirements",
            file=output_file,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        print(
            f"- {idp_security_pct:.1f}% of IdPs have security contacts (IdPs don't require privacy statements)",
            file=output_file,
        )

    print("", file=output_file)

    # Privacy URL Validation Results (if enabled)
    if stats.get("validation_enabled", False):
        urls_checked = stats["urls_checked"]
        if urls_checked > 0:
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100
            broken_pct = (stats["urls_broken"] / urls_checked) * 100

            accessibility_status = (
                "🟢"
                if accessibility_pct >= 90
                else "🟡"
                if accessibility_pct >= 70
                else "🔴"
            )

            print("## 🔗 Privacy URL Validation Results", file=output_file)
            print(
                f"*Technical accessibility analysis of {urls_checked:,} privacy statement URLs*",
                file=output_file,
            )
            print("", file=output_file)

            print(
                f"- **{accessibility_status} Accessible URLs:** {stats['urls_accessible']:,}/{urls_checked:,} ({accessibility_pct:.1f}%)",
                file=output_file,
            )
            print(
                f"- **❌ Broken/Inaccessible URLs:** {stats['urls_broken']:,}/{urls_checked:,} ({broken_pct:.1f}%)",
                file=output_file,
            )
            print("", file=output_file)


def print_federation_summary(federation_stats: dict, output_file=sys.stderr) -> None:
    """Print user-friendly federation-level statistics in markdown format."""
    if not federation_stats:
        print("## 🌍 Federation Analysis", file=output_file)
        print("*No federation data available*", file=output_file)
        return

    # Sort federations by total entities (descending)
    sorted_federations = sorted(
        federation_stats.items(), key=lambda x: x[1]["total_entities"], reverse=True
    )

    print("## 🌍 Federation Analysis", file=output_file)
    print(
        f"*Quality metrics for {len(sorted_federations)} federations*",
        file=output_file,
    )
    print("", file=output_file)

    for federation, stats in sorted_federations:
        total = stats["total_entities"]
        total_sps = stats["total_sps"]
        total_idps = stats["total_idps"]

        if total == 0:
            continue

        # Federation name is already mapped from registration authority
        federation_name = federation

        print(f"### 📍 **{federation_name}**", file=output_file)
        print(
            f"**{total:,} entities** ({total_sps:,} SPs, {total_idps:,} IdPs)",
            file=output_file,
        )
        print("", file=output_file)

        # Privacy coverage for SPs
        if total_sps > 0:
            sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
            privacy_status = (
                "🟢" if sp_privacy_pct >= 80 else "🟡" if sp_privacy_pct >= 50 else "🔴"
            )
            print(
                f"**Privacy Statements:** {privacy_status} {stats['sps_has_privacy']:,}/{total_sps:,} SPs ({sp_privacy_pct:.1f}%)",
                file=output_file,
            )

        # Security coverage breakdown
        total_security_pct = (stats["total_has_security"] / total) * 100
        security_status = (
            "🟢"
            if total_security_pct >= 80
            else "🟡"
            if total_security_pct >= 50
            else "🔴"
        )
        print(
            f"**Security Contacts:** {security_status} {stats['total_has_security']:,}/{total:,} total ({total_security_pct:.1f}%)",
            file=output_file,
        )

        # Detailed breakdown by entity type
        if total_sps > 0 and total_idps > 0:
            sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
            idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
            sp_security_status = (
                "🟢"
                if sp_security_pct >= 80
                else "🟡"
                if sp_security_pct >= 50
                else "🔴"
            )
            idp_security_status = (
                "🟢"
                if idp_security_pct >= 80
                else "🟡"
                if idp_security_pct >= 50
                else "🔴"
            )
            print(
                f"  └─ SPs: {sp_security_status} {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%) • IdPs: {idp_security_status} {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
                file=output_file,
            )
        elif total_sps > 0:
            sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
            sp_security_status = (
                "🟢"
                if sp_security_pct >= 80
                else "🟡"
                if sp_security_pct >= 50
                else "🔴"
            )
            print(
                f"  └─ SPs: {sp_security_status} {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%)",
                file=output_file,
            )
        elif total_idps > 0:
            idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
            idp_security_status = (
                "🟢"
                if idp_security_pct >= 80
                else "🟡"
                if idp_security_pct >= 50
                else "🔴"
            )
            print(
                f"  └─ IdPs: {idp_security_status} {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
                file=output_file,
            )

        # SIRTFI certification coverage (both SPs and IdPs)
        total_sirtfi_pct = (stats["total_has_sirtfi"] / total) * 100
        sirtfi_status = (
            "🟢" if total_sirtfi_pct >= 80 else "🟡" if total_sirtfi_pct >= 50 else "🔴"
        )
        print(
            f"**SIRTFI Certification:** {sirtfi_status} {stats['total_has_sirtfi']:,}/{total:,} ({total_sirtfi_pct:.1f}%)",
            file=output_file,
        )

        # Show entity type breakdown if both SPs and IdPs exist
        if total_sps > 0 and total_idps > 0:
            sp_sirtfi_pct = (stats["sps_has_sirtfi"] / total_sps) * 100
            sp_sirtfi_status = (
                "🟢" if sp_sirtfi_pct >= 80 else "🟡" if sp_sirtfi_pct >= 50 else "🔴"
            )
            print(
                f"  ├─ SPs: {sp_sirtfi_status} {stats['sps_has_sirtfi']:,}/{total_sps:,} ({sp_sirtfi_pct:.1f}%)",
                file=output_file,
            )

            idp_sirtfi_pct = (stats["idps_has_sirtfi"] / total_idps) * 100
            idp_sirtfi_status = (
                "🟢" if idp_sirtfi_pct >= 80 else "🟡" if idp_sirtfi_pct >= 50 else "🔴"
            )
            print(
                f"  └─ IdPs: {idp_sirtfi_status} {stats['idps_has_sirtfi']:,}/{total_idps:,} ({idp_sirtfi_pct:.1f}%)",
                file=output_file,
            )
        elif total_sps > 0:
            sp_sirtfi_pct = (stats["sps_has_sirtfi"] / total_sps) * 100
            sp_sirtfi_status = (
                "🟢" if sp_sirtfi_pct >= 80 else "🟡" if sp_sirtfi_pct >= 50 else "🔴"
            )
            print(
                f"  └─ SPs: {sp_sirtfi_status} {stats['sps_has_sirtfi']:,}/{total_sps:,} ({sp_sirtfi_pct:.1f}%)",
                file=output_file,
            )
        elif total_idps > 0:
            idp_sirtfi_pct = (stats["idps_has_sirtfi"] / total_idps) * 100
            idp_sirtfi_status = (
                "🟢" if idp_sirtfi_pct >= 80 else "🟡" if idp_sirtfi_pct >= 50 else "🔴"
            )
            print(
                f"  └─ IdPs: {idp_sirtfi_status} {stats['idps_has_sirtfi']:,}/{total_idps:,} ({idp_sirtfi_pct:.1f}%)",
                file=output_file,
            )

        # Combined compliance for SPs (if any)
        if total_sps > 0:
            sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
            compliance_status = (
                "🟢" if sp_both_pct >= 80 else "🟡" if sp_both_pct >= 50 else "🔴"
            )
            print(
                f"**Full Compliance:** {compliance_status} {stats['sps_has_both']:,}/{total_sps:,} SPs ({sp_both_pct:.1f}%)",
                file=output_file,
            )

        # Privacy URL Validation Results (if any URLs were checked)
        urls_checked = stats.get("urls_checked", 0)
        if urls_checked > 0:
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100

            accessibility_status = (
                "🟢"
                if accessibility_pct >= 90
                else "🟡"
                if accessibility_pct >= 70
                else "🔴"
            )

            print(
                f"**URL Validation:** {accessibility_status} {stats['urls_accessible']:,}/{urls_checked:,} accessible ({accessibility_pct:.1f}%)",
                file=output_file,
            )

        print("", file=output_file)


def export_federation_csv(federation_stats: dict, include_headers: bool = True) -> None:
    """Export federation statistics to CSV format."""
    writer = csv.writer(sys.stdout)

    # CSV headers - check if validation was enabled for any federation
    validation_enabled = any(
        fed_stats.get("urls_checked", 0) > 0 for fed_stats in federation_stats.values()
    )

    if include_headers:
        headers = [
            "Federation",
            "TotalEntities",
            "TotalSPs",
            "TotalIdPs",
            "SPsWithPrivacy",
            "SPsMissingPrivacy",
            "EntitiesWithSecurity",
            "EntitiesMissingSecurity",
            "SPsWithSecurity",
            "SPsMissingSecurity",
            "IdPsWithSecurity",
            "IdPsMissingSecurity",
            "EntitiesWithSIRTFI",
            "EntitiesMissingSIRTFI",
            "SPsWithSIRTFI",
            "SPsMissingSIRTFI",
            "IdPsWithSIRTFI",
            "IdPsMissingSIRTFI",
            "SPsWithBoth",
            "SPsWithAtLeastOne",
            "SPsMissingBoth",
        ]

        if validation_enabled:
            headers.extend(
                [
                    "URLsChecked",
                    "URLsAccessible",
                    "URLsBroken",
                    "AccessibilityPercentage",
                ]
            )

        writer.writerow(headers)

    # Sort federations by total entities (descending)
    sorted_federations = sorted(
        federation_stats.items(), key=lambda x: x[1]["total_entities"], reverse=True
    )

    for federation, stats in sorted_federations:
        total_sps = stats["total_sps"]
        sp_missing_both = stats["sps_missing_both"]
        sp_has_at_least_one = total_sps - sp_missing_both

        row_data = [
            federation,
            stats["total_entities"],
            stats["total_sps"],
            stats["total_idps"],
            stats["sps_has_privacy"],
            stats["sps_missing_privacy"],
            stats["total_has_security"],
            stats["total_missing_security"],
            stats["sps_has_security"],
            stats["sps_missing_security"],
            stats["idps_has_security"],
            stats["idps_missing_security"],
            stats["total_has_sirtfi"],
            stats["total_missing_sirtfi"],
            stats["sps_has_sirtfi"],
            stats["sps_missing_sirtfi"],
            stats["idps_has_sirtfi"],
            stats["idps_missing_sirtfi"],
            stats["sps_has_both"],
            sp_has_at_least_one,
            sp_missing_both,
        ]

        # Add URL validation data if enabled
        if validation_enabled:
            urls_checked = stats.get("urls_checked", 0)
            urls_accessible = stats.get("urls_accessible", 0)
            urls_broken = stats.get("urls_broken", 0)

            # Calculate accessibility percentage
            accessibility_pct = (
                (urls_accessible / urls_checked * 100) if urls_checked > 0 else 0
            )

            row_data.extend(
                [
                    urls_checked,
                    urls_accessible,
                    urls_broken,
                    f"{accessibility_pct:.1f}%",
                ]
            )

        # Write row
        writer.writerow(row_data)
