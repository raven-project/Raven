from raven.graph_rag.ingestion_service.text_chunker import TextChunker

test_text = """
[{
        "EDB-ID": "52297",
        "size": "95 bytes",
        "Title": "Linux/x86 - Reverse TCP Shellcode (95 bytes)",
        "Author": "Al Baradi Joy",
        "Type": "shellcode",
        "Platform": "i",
        "Published": "2025-05-21",
        "EDB Verified": "✗",
        "Shellcode Code": "↓"
    }]

"""
test_chunker = TextChunker(chunk_size=500, overlap=200)
test_chunks = test_chunker.chunk_text(test_text)
if __name__ == "__main__":
    print(test_chunks)
# Input:
# 在当今的digital era，网络安全已成为企业生存的core competency。随着APT（高级持续性威胁）攻击的激增，传统的firewall和antivirus软件已无法应对sophisticated的攻击手段。企业必须建立zero-trust安全架构，通过continuous monitoring和behavioral analysis实时检测anomalies。同时，员工需要定期接受security awareness training，避免因phishing emails导致credential leakage。云计算时代，云原生安全（Cloud-Native Security）要求采用shift-left策略，在DevOps流程早期嵌入security controls。对于IoT设备激增的OT环境，需部署micro-segmentation隔离关键资产。此外，GDPR等compliance regulations要求企业实施data encryption和access control机制。建议采用AI驱动的SOAR平台实现incident response自动化，并通过threat intelligence sharing提升collective defense能力。
# Output:
# ["In the current digital era, cyber security has become a core competency for business survival", ". With the surge in APT (Advanced Persistent Threat) attacks, traditional firewalls and antivirus software are no longer sufficient to counter sophisticated attack methods", ". Enterprises must establish a zero-trust security architecture, using continuous monitoring and behavioral analysis to detect anomalies in real-time", ". Additionally, employees need regular security awareness training to avoid credential leakage due to phishing emails", ". In the age of cloud computing, cloud-native security requires adopting a shift-left strategy, embedding security controls early in the DevOps process", ". For the OT environment with a surge in IoT devices, micro-segmentation should be deployed to isolate critical assets", ". Moreover, compliance regulations such as GDPR require enterprises to implement data encryption and access control mechanisms", ". It is recommended to adopt an AI-driven SOAR platform for automated incident response and enhance collective defense capabilities through threat intelligence sharing."]
