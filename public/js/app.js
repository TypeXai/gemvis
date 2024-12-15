document.addEventListener("DOMContentLoaded", () => {
  // API Configuration
  const API_URL =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "https://gemini-invoice-processor.onrender.com";

  const uploadForm = document.getElementById("uploadForm");
  const invoiceFile = document.getElementById("invoiceFile");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const resultDiv = document.getElementById("result");

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!invoiceFile.files[0]) {
      alert("Please select a file");
      return;
    }

    const file = invoiceFile.files[0];

    // Validate file type and size
    if (!file.type.match("image.*")) {
      alert("Please upload an image file");
      return;
    }

    if (file.size > 6 * 1024 * 1024) {
      alert("File size should be less than 6MB");
      return;
    }

    try {
      loadingOverlay.style.display = "flex";

      // Create form data for processing
      const formData = new FormData();
      formData.append("file", file);

      // Process with backend
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
        credentials: "omit",
        mode: "cors",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === "success") {
        // Display results
        displayResults(data.invoice_data);
      } else {
        throw new Error(data.error || "Processing failed");
      }
    } catch (error) {
      console.error("Error:", error);
      alert(`Error processing invoice: ${error.message}`);
      resultDiv.style.display = "none";
    } finally {
      loadingOverlay.style.display = "none";
    }
  });

  function displayResults(invoiceData) {
    resultDiv.innerHTML = `
      <h3>Processing Results</h3>
      <div class="table-responsive">
        <table class="table table-bordered">
          <thead>
            <tr>
              <th>תיאור</th>
              <th>כמות</th>
              <th>מחיר יחידה</th>
              <th>סה"כ</th>
            </tr>
          </thead>
          <tbody>
            ${invoiceData.line_items
              .map(
                (item) => `
              <tr>
                <td>${item.description}</td>
                <td class="text-center">${item.quantity}</td>
                <td class="text-center">${formatCurrency(item.unit_price)}</td>
                <td class="text-center">${formatCurrency(item.total)}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="3" class="text-end">סה"כ לפני מע"מ:</td>
              <td class="text-center">${formatCurrency(
                invoiceData.totals.subtotal
              )}</td>
            </tr>
            <tr>
              <td colspan="3" class="text-end">מע"מ (17%):</td>
              <td class="text-center">${formatCurrency(
                invoiceData.totals.tax
              )}</td>
            </tr>
            <tr>
              <td colspan="3" class="text-end"><strong>סה"כ כולל מע"מ:</strong></td>
              <td class="text-center"><strong>${formatCurrency(
                invoiceData.totals.total
              )}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;
    resultDiv.style.display = "block";
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat("he-IL", {
      style: "currency",
      currency: "ILS",
    }).format(amount);
  }
});
