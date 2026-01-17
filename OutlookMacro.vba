' eBay Listing Export Macro for Outlook
' Exports unread emails from Linda folder with eBay URLs and prices
' Output: C:\Users\scott\ebay-automation\email_export.txt

Sub ExportLindaEmails()
    Dim olApp As Outlook.Application
    Dim olNs As Outlook.NameSpace
    Dim olFolder As Outlook.MAPIFolder
    Dim olItem As Object
    Dim fso As Object
    Dim outputFile As Object
    Dim completedFile As Object
    Dim completedItems As Object
    Dim subject As String
    Dim body As String
    Dim itemId As String
    Dim price As String
    Dim outputPath As String
    Dim completedPath As String
    Dim count As Integer
    Dim line As String

    outputPath = "C:\Users\scott\ebay-automation\email_export.txt"
    completedPath = "C:\Users\scott\ebay-automation\completed_items.txt"

    Set olApp = Outlook.Application
    Set olNs = olApp.GetNamespace("MAPI")
    Set fso = CreateObject("Scripting.FileSystemObject")

    ' Load completed items to skip
    Set completedItems = CreateObject("Scripting.Dictionary")
    If fso.FileExists(completedPath) Then
        Set completedFile = fso.OpenTextFile(completedPath, 1)
        Do While Not completedFile.AtEndOfStream
            line = Trim(completedFile.ReadLine)
            If Len(line) > 0 Then
                completedItems(line) = True
            End If
        Loop
        completedFile.Close
    End If

    ' Find Linda folder - search in all accounts
    Set olFolder = Nothing
    Dim store As Outlook.store
    Dim rootFolder As Outlook.MAPIFolder
    Dim subFolder As Outlook.MAPIFolder

    For Each store In olNs.Stores
        On Error Resume Next
        Set rootFolder = store.GetRootFolder
        If Not rootFolder Is Nothing Then
            For Each subFolder In rootFolder.Folders
                If LCase(subFolder.Name) = "linda" Then
                    Set olFolder = subFolder
                    Exit For
                End If
            Next subFolder
        End If
        On Error GoTo 0
        If Not olFolder Is Nothing Then Exit For
    Next store

    If olFolder Is Nothing Then
        MsgBox "Could not find Linda folder!", vbExclamation
        Exit Sub
    End If

    ' Create output file
    Set outputFile = fso.CreateTextFile(outputPath, True)
    outputFile.WriteLine "# eBay Email Export - " & Now()
    outputFile.WriteLine "# Format: ItemID|Price|Subject"
    outputFile.WriteLine ""

    count = 0

    ' Process unread emails
    For Each olItem In olFolder.Items
        If TypeName(olItem) = "MailItem" Then
            If olItem.UnRead = True Then
                subject = olItem.subject
                body = olItem.body

                ' Extract eBay item ID from URL
                itemId = ExtractEbayItemId(body)
                If itemId = "" Then itemId = ExtractEbayItemId(subject)

                ' Skip if already completed
                If itemId <> "" And Not completedItems.Exists(itemId) Then
                    ' Extract price
                    price = ExtractPrice(body)
                    If price = "" Then price = ExtractPrice(subject)

                    ' Write to file
                    outputFile.WriteLine itemId & "|" & price & "|" & Left(subject, 60)
                    count = count + 1
                End If
            End If
        End If

        ' Limit to prevent hanging
        If count >= 50 Then Exit For
    Next olItem

    outputFile.Close

    MsgBox "Exported " & count & " emails to:" & vbCrLf & outputPath, vbInformation
End Sub

Function ExtractEbayItemId(text As String) As String
    ' Find eBay item ID from URL pattern /itm/NUMBERS
    Dim regex As Object
    Dim matches As Object

    Set regex = CreateObject("VBScript.RegExp")
    regex.Pattern = "/itm/(\d+)"
    regex.Global = False

    If regex.Test(text) Then
        Set matches = regex.Execute(text)
        ExtractEbayItemId = matches(0).SubMatches(0)
    Else
        ExtractEbayItemId = ""
    End If
End Function

Function ExtractPrice(text As String) As String
    ' Find price pattern like "List new $79.50" or "$79.50"
    Dim regex As Object
    Dim matches As Object

    Set regex = CreateObject("VBScript.RegExp")
    regex.Pattern = "List\s+new\s+\$?([\d,]+\.?\d*)"
    regex.IgnoreCase = True
    regex.Global = False

    If regex.Test(text) Then
        Set matches = regex.Execute(text)
        ExtractPrice = matches(0).SubMatches(0)
    Else
        ' Try just dollar amount
        regex.Pattern = "\$([\d,]+\.\d{2})"
        If regex.Test(text) Then
            Set matches = regex.Execute(text)
            ExtractPrice = matches(0).SubMatches(0)
        Else
            ExtractPrice = ""
        End If
    End If
End Function
