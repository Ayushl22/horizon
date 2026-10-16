param([string]$InputPath, [string]$OutputPath)
# Artifact-only conversion in a separate invisible Word instance. Never modifies
# the source document or any document already open in the user's Word session.
$wordApp = $null
$reviewDoc = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $reviewDoc = $wordApp.Documents.Open($InputPath, $false, $true, $false)
    $reviewDoc.Fields.Update() | Out-Null
    $reviewDoc.Repaginate()
    $reviewDoc.ExportAsFixedFormat($OutputPath, 17)
    Write-Output "Rendered PDF: $OutputPath"
} finally {
    if ($null -ne $reviewDoc) { $reviewDoc.Close(0); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($reviewDoc) }
    if ($null -ne $wordApp) { $wordApp.Quit(); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordApp) }
}
